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
from openai import OpenAI

app=FastAPI()

health_records_directory=os.getenv('HEALTH_RECORDS_DIRECTORY')
health_records_lookup=f'{health_records_directory}/ehr_lookup.json'

def search_key_in_json(json_obj, search_term):
    search_term = search_term.lower()
    
    def recursive_search(d):
        for key, value in d.items():
            if key.lower() == search_term:
                return value
            elif isinstance(value, dict):
                result = recursive_search(value)
                if result is not None:
                    return result
        return None
    
    return recursive_search(json_obj)

def json_to_formatted_string(json_obj):
    def parse_dict(d, level=0):
        lines = []
        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"{' ' * (level * 2)}{key}:")
                lines.extend(parse_dict(value, level + 1))
            elif isinstance(value, list):
                lines.append(f"{' ' * (level * 2)}{key}:")
                for item in value:
                    lines.append(f"{' ' * ((level + 1) * 2)}- {item}")
            else:
                lines.append(f"{' ' * (level * 2)}- {key}: {value}")
        return lines
    
    formatted_string = "\n".join(parse_dict(json_obj))
    return formatted_string

def formatted_string_to_json(formatted_string):
    lines = formatted_string.split("\n")
    
    def parse_lines(lines, level=0):
        obj = {}
        i = 0
        while i < len(lines):
            line = lines[i]
            current_level = len(re.match(r'\s*', line).group(0)) // 2
            
            if current_level < level:
                break
            
            if current_level == level:
                if ": " in line:
                    key, value = line.strip().split(": ", 1)
                    obj[key.strip()] = value.strip()
                elif line.strip().endswith(":"):
                    key = line.strip()[:-1]
                    i, nested_obj = parse_lines(lines[i + 1:], level + 1)
                    obj[key.strip()] = nested_obj
            
            i += 1
        return i, obj
    
    _, json_obj = parse_lines(lines)
    return json_obj

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
        "temperature": 0,
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
            
async def gpt_json(prompt,max_tokens):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'default-key'))
    messages = [
           {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content":  f'''{prompt}'''},
            ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        temperature=0,
        response_format={ "type": "json_object" },
        messages=messages
        )
    result=response.choices[0].message.content
    return result

async def extract_intent_and_content(query:str,intent:str):
    if intent.lower() == 'create':
        create_prompt=f'''You are an AI designed to help doctors to automate Electronic Health Records, you will be given a query by a 
         Doctor, where you are asked to create a medical record for a patient.
    You need to create a Medical record of the patient based on the information provided by the 
     doctor, and structure it into a json format with headings and subheadings along with the date mentioned in the query.
    Examples of headings and its subheadings:
    Heading: Patient Information ; Subheadings: Patient id,Name, Age, Gender, Date of Birth, Address, Phone Number, Blood Group, etc
    Heading: Chief Complaints
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
        output=await gpt_json(create_prompt,1000)
        #print(output)
        report_json=json.loads(output)
        patient_id_exists=True
        result=search_key_in_json(report_json,'patient id')
        if not result:
            patient_id_exists=False
            # report_json['Patient Information']['Patient id'] = ''
            # json.dumps(report_json, indent=4)
            patient_info = report_json['Patient Information']
            new_patient_info = {'Patient id': ''}  # You can replace '12345' with the actual patient id
            new_patient_info.update(patient_info)
            # Update the original dictionary
            report_json['Patient Information'] = new_patient_info
            json.dumps(report_json, indent=4)
            
            
        print('patient id exists',patient_id_exists)
        #Convert report_json to report, which is some kind of text format of json, but looks human readable
        report = json_to_formatted_string(report_json)
        print("report:\n", report_json)
        # json_obj = formatted_string_to_json(formatted_string)
        # print("Reconstructed JSON:\n", json.dumps(json_obj, indent=4))
        
        # # We use the lookahead assertion (?=Summary:) to stop at the "Summary" section
        # report_match = re.search(r"^Patient Information:(.+)$", output, re.DOTALL | re.MULTILINE)
        # if report_match:
        #     report = report_match.group(1).strip()
        if not os.path.exists(health_records_directory):
            os.makedirs(health_records_directory)
        
        file_id=uuid.uuid4().hex
        file_name=f'{file_id}.txt'
        file_path=os.path.join(health_records_directory,file_name)
        # else:
        #     report = None
        
        # print(patient_id_exists)
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
    elif intent.lower()=='update': 
        update_prompt=f'''You are an AI designed to help doctors to automate Electronic Health Records, you will be given a query by a 
         Doctor, where you are asked to update the medical record of an existing patient. You need to extract information from the query and structure it into json format with various headings and subheadings that occur in a medical record, like:
        Patient details(Name, Patient id, age,etc), Test Reports and Results, Medical History, Prescription, Condition Improvements, Checks and Follow up,etc.
         You must keep the Patient id field blank, in case it is not provided.
         You must not mention a Heading or Subheading in the output, if its information isnt given in the query.
         You must clearly mention numerical results of the test, and you must structure the report chronologically.
    This is the query given by the doctor: 
    {query}\n'''
        output=await gpt_json(update_prompt,300)
        #print(output)
        report_json=json.loads(output)
        patient_id_exists=True
        result=search_key_in_json(report_json,'patient id')
        if not result:
            patient_id_exists=False
            new_report_json = {
                "Patient id": result
            }
            for key, value in report_json.items():
                if key.lower() != "patient details":
                    new_report_json[key] = value
        #print(new_report_json)
        report = json_to_formatted_string(new_report_json)
        print("report:\n", report)
        # patient_id_match = re.search("Patient id: (.+)$", output,re.IGNORECASE|re.MULTILINE)
        # if patient_id_match:
        #     patient_id=patient_id_match.group(1)
        #     print('patient_id',patient_id)
        #     patient_id_exists=True
        # else:
        #     patient_id=None
        # file_id=uuid.uuid4().hex
        # file_name=f'{file_id}.txt'
        # file_path=os.path.join(health_records_directory,file_name)
        if not os.path.exists(health_records_directory):
            os.makedirs(health_records_directory)
        
        file_id=uuid.uuid4().hex
        file_name=f'{file_id}.txt'
        file_path=os.path.join(health_records_directory,file_name)
        
        # result =  re.search(r'Patient id: [^\n]*[\r\n]+([^\S\r\n]*.*$)', output, re.IGNORECASE|re.DOTALL)
        # if result:
        #     extracted_text = result.group(1)
        #     print('extracted: ',extracted_text)
        # else:
        #     print("No match found.")
        
        return (file_path,report,patient_id_exists)# need to break out the actual output
    else:
        return ('No predefined intents match')
        

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
    intent_prompt=f'''You are an AI designed to help doctors automate Electronic Health Records (EHR). You will be given a query by a doctor, which could involve creating a new medical record for a patient, reading existing medical records for a patient, updating the medical record for a patient, or deleting the medical records for a patient.

Your task is to classify the intent of the query into one of the following categories: Create, Read, Update, or Delete.

Please use the following criteria to classify the intent:

- **Create:** The query asks to create a new medical record.
  Example: "Create a new record for John Doe with the diagnosis of hypertension."

- **Read:** The query asks to retrieve or read existing medical records without making any changes.
  Example: "Retrieve the medical history for Jane Smith."

- **Update:** The query asks to modify or add or update some information.
  Example: "Update the diagnosis for John Doe to include diabetes."

- **Delete:** The query asks to remove or delete existing medical records or specific information within them.
  Example: "Delete the medical record for patient ID 12345."

In your output, you must write the intent clearly as:
Intent: <intent of the query>

This is the query given by the doctor:
{query}\n
    '''
    # output_intent=await gpt_processor(intent_prompt,100)
    # intent_match = re.search(r"^Intent: (\w+)", output_intent, re.MULTILINE)
    # if intent_match:
    #     intent = intent_match.group(1)
    # else:
    #     intent = None
    # print('Intent: ',intent)
    output_intent=await gpt_json(intent_prompt,100)
    output_intent=json.loads(output_intent)
    intent=output_intent["Intent"]
    print("intent",intent)
    output_task=await extract_intent_and_content(query,intent)
    # print('output_task: ',output_task)
    # #Heavy regex to be employed here- separate out the intent and the following text
    if intent.lower()=='create':
        #send the report to streamlit for the user to edit
        return {"Intent": intent,"Generated Report": output_task[1],"File Path": output_task[0],"Patient id exists":output_task[2]}
    # elif intent.lower()=='read':
    #     records=await search_and_load_summary(output_task[1])
    #     if records:
    #         #print(records)
    #         #Taking multiple records as of now
    #         result=await execute_task_on_records(records[0],output_task[2])   
    #         print(result)
    #     else:
    #         print('No matching records found')
    #     return{"read result":result}
    elif intent.lower()=='update':
        return {"Intent": intent,"File Path":output_task[0],"Updated Report": output_task[1],"Patient id exists":output_task[2]}
    # else:
    #     return{'undefined':output_task}

@app.post("/save_report/")
async def save_report(request: Request):
    data=await request.json()
    print('data',data)
    report=data.get('report','')
    file_path=data.get('file_path', '')
    print('file_path_prior',file_path)
    intent=data.get('intent','')
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
                        value['entries']=value.get('entries', 1) + 1 #no. of entries to the same record- no updations means a single
                        patient_id_exists_in_records=True
                        break
            with open(health_records_lookup, 'w') as lookup_file:
                json.dump(lookup_data, lookup_file, indent=4)
    else:
        patient_id=None
        return {'message':'Patient id is not provided'}
    
    if patient_id_exists_in_records:
        print('patient record already exists')
        #Add to existing patient record, no changes to summary required
        #Regex out the content and remove the patient id
        result =  re.search(r'Patient id: [^\n]*[\r\n]+([^\S\r\n]*.*$)', report, re.IGNORECASE|re.DOTALL)
        if result:
            extracted_text = result.group(1)
            print('extracted: ',extracted_text)
        else:
            print("No match found.")
         
        now = datetime.datetime.now()
        date_format = now.strftime("%d/%m/%Y")
        time_format = now.strftime("%H:%M")
        print(file_path)
        print('extracted: ',extracted_text)
        with open(file_path,'a') as file:
            file.write('\n\n')
            file.write(f'Record Entry: {date_format} {time_format}\n\n')
            file.write(extracted_text)
            file.write('\n')
        print('report saved')
    else:
        print(intent)
        print(intent.lower())
        if intent.lower()=='update':
            print('inside the condition')
            return {'message':'Patient id does not exist in the database'}
        print('condition failed')
        #Intent is create
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