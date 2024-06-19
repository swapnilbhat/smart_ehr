from fastapi import FastAPI,Request
from pydantic import BaseModel
import motor.motor_asyncio
from bson import ObjectId
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
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

app=FastAPI()

# MongoDB connection
MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.health_records
ehr_collection = database.get_collection("ehr")
patient_lookup=database.get_collection("patient_lookup")

# Pydantic model for EHR
class EHRModel(BaseModel):
    entry: int
    patient_id: str
    report: dict

# Helper function to convert BSON to JSON
def ehr_helper(ehr) -> dict:
    return {
        "id": str(ehr["_id"]),
        "entry": ehr["entry"],
        "patient_id": ehr["patient_id"],
        "report": ehr["report"]
    }

# Insert a document into the MongoDB collection
#@app.post("/add_record/", response_model=EHRModel)
async def add_record(entry,patient_id,report):
    now = datetime.datetime.now()
    date_format = now.strftime("%d/%m/%Y")
    time_format = now.strftime("%H:%M")
    report_mod = {
        'Record Entry': {
            'Datetime':now,
            'Date': date_format,
            'Time': time_format
        }
    }
    report_mod.update(report)
    # Create the record to be inserted
    record = {
        'entry': entry,
        'patient_id': patient_id,
        'report': report_mod
    }
    new_record = await ehr_collection.insert_one(record)
    print(f'Record added for patient_id: {patient_id}')
    # Update the lookup table
    lookup_result = await patient_lookup.update_one(
        {'patient_id': patient_id},
        {'$inc': {'record_count': 1}},
        upsert=True
    )
    created_record = await ehr_collection.find_one({"_id": new_record.inserted_id})
    
    return created_record

async def get_patient_record_count(patient_id):
    patient_record = await patient_lookup.find_one({'patient_id': patient_id})
    if patient_record:
        return patient_record['record_count']
    else:
        return 0
    
#@app.post("/print_record/", response_model=EHRModel)
async def print_report(patient_id):
    # Retrieve all reports for the given patient_id
    records = await ehr_collection.find({'patient_id': patient_id}).sort('entry').to_list(None)
    # Check if records exist
    if not records:
        print(f'No records found for patient_id: {patient_id}')
        return
    
    print('found records')
    # Create a PDF document
    pdf_file = f'{patient_id}_report.pdf'
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter
    
    first_entry = True  # Flag to check for the first entry
    
    for record in records:
        entry = record['entry']
        report = record['report']
        
        report=json_to_formatted_string(report)
        
        # Create a new page for each entry
        if not first_entry:
            c.showPage()  # Create a new page for each subsequent entry
        first_entry = False
        
        # Print entry number at the top
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 50, f"Entry Number: {entry}")
        
        # Print the report content
        y_position = height - 100
        text_lines = report.split('\n')
        c.setFont("Helvetica", 10)
        
        for line in text_lines:
            # Ensure the text wraps if it's too long
            wrapped_lines = []
            while len(line) > 80:  # 80 characters per line for wrapping
                wrapped_lines.append(line[:80])
                line = line[80:]
            wrapped_lines.append(line)
            
            for wrapped_line in wrapped_lines:
                if y_position < 100:  # Avoid printing too close to the bottom
                    c.showPage()
                    y_position = height - 100
                    c.setFont("Helvetica", 10)
                c.drawString(100, y_position, wrapped_line)
                y_position -= 12  # Adjust line spacing for better readability
        
        # Add a line separator between reports
        c.line(50, y_position, width - 50, y_position)
        y_position -= 20  # Additional spacing before the next entry
    
    c.save()
    print(f'Report for patient_id {patient_id} has been saved to {pdf_file}')

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
         The records are present in a MongoDB database, so the text query needs to be converted into a MongoDB query.
         Every record has the following fields in MongoDB:
         entry: This is the visit number
         patient_id: Unique id of each patient
         report: Contains the entire medical report of the patient
         report.Record Entry.Datetime: This is the datetime at which the report was created
         report.Chief Complaints.Complaints : Contains the problems the patient was feeling when they went to the doctor
         Your output must be the MongoDB query in JSON format:
         db_query:<MongoDB query>
         
         This is the query given by the doctor: 
         {query}\n'''
        output=await gpt_json(read_prompt,100)
        print('db_output',output)
        output=json.loads(output)
        
        # attribute_name_search=re.search("^Name of Attribute: (.+)$",output, re.MULTILINE)
        # if attribute_name_search:
        #     attribute_name = attribute_name_search.group(1)
        # else:
        #     attribute_name = None
            
        # attribute_value_search=re.search("^Value of the Attribute: (.+)$",output, re.MULTILINE)
        # if attribute_value_search:
        #     attribute_value = attribute_value_search.group(1)
        # else:
        #     attribute_value = None
        
        # task_search=re.search("^Task: (.+)$",output, re.MULTILINE)
        # if task_search:
        #     task = task_search.group(1)
        # else:
        #     task = None
        
        return   
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
        print('json output',output)
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
        else:
            new_report_json = {
                "Patient id": result
            }
            for key, value in report_json.items():
                if key.lower() != "patient details":
                    new_report_json[key] = value
                    
        print('patient id exists',patient_id_exists)
        print('new report',new_report_json)
        report = json_to_formatted_string(new_report_json)
        print("report:\n", report)
        
        if not os.path.exists(health_records_directory):
            os.makedirs(health_records_directory)
        
        file_id=uuid.uuid4().hex
        file_name=f'{file_id}.txt'
        file_path=os.path.join(health_records_directory,file_name)
        
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

async def extract_id_and_json_report(report:str):
    summary_prompt = f'''You are an AI designed to help doctors to automate Electronic Health Records, you will be provided with the medical record of a patient as input, and you must convert that medical record to json format.
    You must write the keys in the json according to the headings and subheadins in the record.
    You must extract the Patient id from the medical record,if its provided and give that as output separately.
    If Patient id is not provided in the medical record, you must return an empty string in the output.
    Your output must be in json format as follows:
    Patient id: <patient id>
    Report :<report in json format>
    
    The medical report of the patient:
    {report}'''
    output=await gpt_json(summary_prompt,1000)
    print('id and json report', output)
    return output

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
    elif intent.lower()=='read':
        records=await search_and_load_summary(output_task[1])
        if records:
            #print(records)
            #Taking multiple records as of now
            result=await execute_task_on_records(records[0],output_task[2])   
            print(result)
        else:
            print('No matching records found')
        return{"read result":result}
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
    print('intent',intent)
    #Patient id will be provided-no case where it wont be there
    output_json=await extract_id_and_json_report(report)
    output=json.loads(output_json)
    patient_id=output['Patient id']
    print('patient id gpt',patient_id)
    report=output['Report']
    print('report json gpt',report)
    entry=1
    
    #Read the report and find patient id
    patient_id_exists_in_records=False
    
    if patient_id:
        record_count = await get_patient_record_count(patient_id)
        if record_count!=0:
            patient_id_exists_in_records=True
            entry=record_count+1
    else:
        return {'message':'Patient id is not provided'}
    
    if patient_id_exists_in_records:
        print('patient id exists in records')
        updated_record = await add_record(entry, patient_id, report)
        print(updated_record)
        await print_report(patient_id)
    else:
        print('Patient id doens\'t exist in records, creating a new report if intent is create')
        print(intent)
        if intent.lower()=='update':
            print('inside the condition')
            return {'message':'Patient id does not exist in the database'}
        
        created_record = await add_record(entry, patient_id, report)
        print(created_record)
        
        await print_report(patient_id)
      
  
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)