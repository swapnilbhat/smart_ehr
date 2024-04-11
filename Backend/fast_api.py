from fastapi import FastAPI,Request
import uvicorn
import aiohttp
import openai
import json
import os
import re
import uuid
import time
import datetime

app=FastAPI()

health_records_directory='/home/blu/ai/smart_ehr/health_records'
health_records_lookup='/home/blu/ai/smart_ehr/health_records/ehr_lookup.json'

async def gpt_processor(prompt,max_tokens):
    
    openai.api_key = os.getenv('OPENAI_API_KEY', 'default-key')

    # Headers for the OpenAI API request
    headers = {
        "Authorization": f"Bearer {openai.api_key}",
        "Content-Type": "application/json"
    }

    # Body for the OpenAI API request
    data = json.dumps({
        "model": "gpt-3.5-turbo", # Specify the GPT-4 model you're using
        "messages":[
      {
        "role": "user",
        "content": prompt
      }],
        "temperature": 0.01,
        "max_tokens": max_tokens,
    })
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, data=data) as response:
            if response.status:
                response_data = await response.json()
                intent = response_data['choices'][0]['message']['content']
                return intent
            else:
                return "Error: Failed to receive a valid response from OpenAI API"

async def extract_intent_and_content(query:str,intent:str):
    if intent.lower() == 'create':
        create_prompt=f'''You are an AI designed to help doctors to automate Electronic Health Records, you will be given a query by a 
         Doctor, where you are asked to create a medical record for a patient.
    You need to create a Medical record of the patient based on the information provided by the 
     doctor, and structure it into a proper format with headings and subheadings along with the date mentioned in the query.
    Examples of headings and its subheadings:
    Heading: Patient Information ; Subheadings: Patient id,Name, Age, Gender, Date of Birth, Address, Phone Number, Blood Group, etc
    Heading: General Information
    Heading: Medical History;  
    Heading: Surgical Procedure; Subheadings: Procedure Name, Date of Surgery, Surgeon, Procedure Details, etc
    Heading: Test conducted; Subheadings: Tests conducted and their results along with date
    Heading: Post Operative Care
    Heading: Discharge Instructions
    Heading: Signature     
    The above list is not exhaustive and you can create Headings on your own to group the text.You must add content under the relevant 
    heading based on how it appears in the query. 
    You must not mention a Heading or Subheading in the output, if its information isnt given in the query.
    You must clearly mention numerical results of the test, and you must structure the report chronologically. 
    You must give the medical record for the patient as output  
    This is the query given by the doctor: 
    {query}\n'''
        output=await gpt_processor(create_prompt,650)
    #     After the medical record give a summary of the medical record in MAX 40 words as Summary: <summary>, mentioning key 
    # details like Personal Information(Name,Age,Gender), Surgical Procedure and Medical History. Dont mention the headings in the 
    # summary. This summary should contain only the key details and should be a single string on a single line.
        #print(output)
        # # Extract Medical Report
        patient_id_exists=False
        patient_id_match = re.search(r"Patient id: (.+)$", output,re.IGNORECASE|re.MULTILINE)
        if patient_id_match:
            patient_id=patient_id_match.group(1)
            print('patient_id',patient_id)
            patient_id_exists=True
        else:
            patient_id=None
        # We use the lookahead assertion (?=Summary:) to stop at the "Summary" section
        report_match = re.search(r"^Patient Information:(.+)$", output, re.DOTALL | re.MULTILINE)
        if report_match:
            report = report_match.group(1).strip()
            if not os.path.exists(health_records_directory):
                os.makedirs(health_records_directory)
            file_id=uuid.uuid4().hex
            file_name=f'{file_id}.txt'
            file_path=os.path.join(health_records_directory,file_name)
        else:
            report = None
        
        # # Extract Summary
        # summary_match = re.search(r"^Summary: (.+)$", output, re.MULTILINE)
        # if summary_match:
        #     summary = summary_match.group(1)
        # else:
        #     summary = None
        
        # if os.path.exists(health_records_lookup):
        #     with open(health_records_lookup,'r') as lookup_file:
        #         lookup_data=json.load(lookup_file)
        # else:
        #     lookup_data={}
        
        # lookup_data[file_id] = {
        #     "file_path": file_path,
        #     "patient_id":patient_id,
        #     "summary": summary
        # }
        # with open(health_records_lookup,'w') as lookup_file:
        #     json.dump(lookup_data, lookup_file, indent=4)
        print(patient_id_exists)
        return (file_path,report,patient_id_exists)
    
    elif intent.lower()=='read':
        read_prompt=f'''You are an AI designed to help doctors to automate Electronic Health Records, you will be given a query by a 
         Doctor, where you are asked to read a medical record for a patient.
         The doctor wants you to first search for a patient based on a specifc attribute(like Name, Age, Surgical Procedure,etc) and the value of that attribute(like Name is Arjun, so Name is the attribute and Arjun is the value) in the Electronic Health Records, and retrive his data. After retrieval the doctor wants you to perfom a task on the retrieved record.
         Examples of tasks are: Retrieve Blood Pressure of the patient, Read glucose levels,etc
         You need to write the output in the following format:
         Name of Attribute:<search attribute mentioned by the doctor>
         Value of the Attribute:<value of the attribute mentioned by the doctor>
         Task: <task required to be perfomed on the data, must not contain the Name or value of the attribute.>
         This is the query given by the doctor: 
         {query}\n'''
        output=await gpt_processor(read_prompt,100)
        attribute_name_search=re.search("^Name of Attribute: (.+)$",output, re.MULTILINE)
        if attribute_name_search:
            attribute_name = attribute_name_search.group(1)
        else:
            attribute_name = None
            
        attribute_value_search=re.search("^Value of the Attribute: (.+)$",output, re.MULTILINE)
        if attribute_value_search:
            attribute_value = attribute_value_search.group(1)
        else:
            attribute_value = None
        
        task_search=re.search("^Task: (.+)$",output, re.MULTILINE)
        if task_search:
            task = task_search.group(1)
        else:
            task = None
        
        return (attribute_name,attribute_value,task)     

async def generate_summary(report:str):
    summary_prompt = f'''You are an AI designed to help doctors to automate Electronic Health Records, you will be provided with the medical record of a patient as input, and you must generate a summary of that medical record as output.
    The summary should be given as Summary:<summary>, in Maximum 40 words. You must not exceed this word limit.
    The summary must mention key details like Personal Information(Name,Age,Gender), Surgical Procedure and Medical History. This summary should contain only the key details and should be a single string on a single line.
    The medical report of the patient:
    {report}'''
    output=await gpt_processor(summary_prompt,300)
    summary_match = re.search(r"^Summary: (.+)$", output, re.MULTILINE)
    if summary_match:
        summary = summary_match.group(1)
    else:
        summary = None
    
    return summary
    
async def search_and_load_summary(attribute_value:str):
    #Search through existing record summaries and find matches(one or more)
     if os.path.exists(health_records_lookup):
         with open(health_records_lookup,'r') as lookup_file:
             lookup_data=json.load(lookup_file)
     else:
         return None
     #search for matching summaries
     matching_ids = [uid for uid, info in lookup_data.items() if attribute_value.lower() in info['summary'].lower()]
     #load the records
     records=[]
     for uid in matching_ids:
         with open(lookup_data[uid]['file_path'],'r') as file:
             records.append(file.read())
     return records

async def execute_task_on_records(record, task):
    task_prompt = f'''You are an AI designed to help doctors to automate Electronic Health Records, you will be given a task by a 
         Doctor, the task is to be executed on a patient health record which will be provided. You must perform the task only in the context of the patient health record, and should provide provide the output, on a newline as Output:<output of the task>.
         The length of the output must not exceed 100 words.
    Examples of the task:
        read the medicines prescribed to the patient, tell what were the blood sugar levels of the patient,etc.
        In case the context does not have sufficient or relevant information. Your Output must be "The health record does not contain the necessary information."
    The medical record for the patient is as follows:\n{record}\nBased on this record, {task}\n
    Write the output of the task.
    '''
    output=await gpt_processor(task_prompt,300)
    output_search=re.search("^Output: (.+)$",output, re.MULTILINE)
    if output_search:
        output = output_search.group(1)
    else:
        output_search = None
    return output
    

@app.post("/process_request/")
async def process_request(request: Request):
    data=await request.json()
    query=data['query'].strip()
    #print(query)
    #Intent classification here
    intent_prompt=f'''You are an AI designed to help doctors to automate Electronic Health Records, you will be given a query by a Doctor, where he may ask you to create a medical record for a patient, read existing medical records for a patient, update the medical record for a patient or delete the medical records for a patient.
    Your task is to classify the intent of the query into Create, Read , Update or Delete.
    In your output, you must write the intent clearly as
    Intent: <intent of the query>
     This is the query given by the doctor: 
    {query}\n
    '''
    output_intent=await gpt_processor(intent_prompt,100)
    intent_match = re.search(r"^Intent: (\w+)", output_intent, re.MULTILINE)
    if intent_match:
        intent = intent_match.group(1)
    else:
        intent = None
    print(intent)
    output_task=await extract_intent_and_content(query,intent)
    
    #Heavy regex to be employed here- separate out the intent and the following text
    if intent.lower()=='create':
        #send the report to streamlit for the user to edit
        return {"Intent": intent,"Generated Report": output_task[1],"File Path": output_task[0],"Patient id exists":output_task[2]}
        #return{"intent":f"{intent}","Generated_unique_id":f"{output_task[0]}","Patient Summary":f"{output_task[1]}"}
    elif intent.lower()=='read':
        records=await search_and_load_summary(output_task[1])
        if records:
            #print(records)
            result=await execute_task_on_records(records[0],output_task[2])   
            print(result)
        else:
            print('No matching records found')
        return{"attribute name":f"{output_task[0]}","attribute value":f"{output_task[1]}","task":f"{output_task[2]}"}
    else:
        return{'message':'no intents match'}

@app.post("/save_report/")
async def save_report(request: Request):
    data=await request.json()
    report=data['report']
    file_path=data['file_path']
    #Patient id will be provided-no case where it wont be there
    #Read the report and find patient id
    patient_id_exists_in_records=False
    patient_id_match = re.search(r"Patient id: (.+)$", report,re.IGNORECASE|re.MULTILINE)
    if patient_id_match:
        patient_id=patient_id_match.group(1)
        print('patient_id',patient_id)
        if os.path.exists(health_records_lookup):
            with open(health_records_lookup,'r') as lookup_file:
                lookup_data=json.load(lookup_file)
                for _, value in lookup_data.items(): #Is this O(n)?
                    if 'patient_id' in value and value['patient_id'] == patient_id:
                        file_path= value['file_path'] #overwrite existing file path, and dont change the summary
                        entries=value['entries'] #no. of entries to the same record- no updations means a single entry
                        patient_id_exists_in_records=True
    else:
        patient_id=None
        return {'message':'Patient id is not provided'}
    
    if patient_id_exists_in_records:
        pass
    else:
        file_name = file_path.split('/')[-1]
        # Now remove the extension '.txt'
        file_id = file_name.split('.')[0] #required for json
        #Get the summary for the record
        summary=await generate_summary(report)
        #write to file and to the ehr lookup
        #current date and time
        now = datetime.datetime.now()
        date_format = now.strftime("%d/%m/%Y")
        time_format = now.strftime("%H:%M")
        with open(file_path,'w') as file:
            file.write(f'Record Entry: {date_format} {time_format}\n\n')
            file.write(report)
            file.write('\n')
        print('report saved')

        if os.path.exists(health_records_lookup):
            with open(health_records_lookup,'r') as lookup_file:
                lookup_data=json.load(lookup_file)
        else:
            lookup_data={}
        
        lookup_data[file_id] = {
            "file_path": file_path,
            "patient_id":patient_id,
             "entries":1,
             "summary": summary
        }
        with open(health_records_lookup,'w') as lookup_file:
            json.dump(lookup_data, lookup_file, indent=4)    
  
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)