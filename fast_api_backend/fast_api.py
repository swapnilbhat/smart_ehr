from fastapi import FastAPI,Request,HTTPException,File, UploadFile
from fastapi.responses import FileResponse
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
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes
import pytesseract
import io

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your specific needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.health_records
ehr_collection = database.get_collection("ehr_2")
patient_lookup=database.get_collection("patient_lookup_2")
REPORTS_DIR = 'reports/'
# Pydantic model for EHR
class EHRModel(BaseModel):
    entry: int
    patient_id: str
    report: dict

class Query(BaseModel):
    query:str

class PatientID(BaseModel):
    patient_id: str
    
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
    
async def print_report(patient_id):
    # Retrieve all reports for the given patient_id
    records = await ehr_collection.find({'patient_id': patient_id}).sort('entry').to_list(None)
    # Check if records exist
    if not records:
        print(f'No records found for patient_id: {patient_id}')
        return
    
    print('found records')
    # Create a PDF document
    HEADER_IMAGE='./kem_logo.png'
    pdf_file = f'{REPORTS_DIR}{patient_id}_report.pdf'
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter

    # Define margins
    margin_left = inch
    margin_right = inch
    margin_top = inch
    margin_bottom = inch

    first_entry = True  # Flag to check for the first entry

    for record in records:
        entry = record['entry']
        report = record['report']
        
        report = json_to_formatted_string(report)
        
        # Create a new page for each entry
        if not first_entry:
            c.showPage()  # Create a new page for each subsequent entry
        first_entry = False

        # Draw the header
        #c.drawImage(HEADER_IMAGE, margin_left, height - margin_top, width=2*inch, preserveAspectRatio=True, mask='auto')
        try:
            c.drawImage(HEADER_IMAGE, margin_left, height - margin_top -1.8*inch, width=1*inch, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error loading image: {e}")
        c.setFont("Helvetica-Bold", 14)
        #c.drawString(margin_left + 2.1 * inch, height - margin_top + 0.2 * inch, "Your Report Header Text")
        c.drawString(margin_left + 2.1 * inch, height - margin_top + 0.5 * inch, "Arista Surge Medical Center")
        c.setFont("Helvetica", 12)
        c.drawString(margin_left + 2.1 * inch, height - margin_top + 0.2 * inch, "123 Medical Way, Health City, CA 12345")
        c.drawString(margin_left + 2.1 * inch, height - margin_top, "Phone: (123) 456-7890")

        # Draw the entry number
        c.setFont("Helvetica", 12)
        c.line(margin_left, height - margin_top - 0.3 * inch, width - margin_right, height - margin_top - 0.3 * inch)
        c.drawString(margin_left, height - margin_top - 0.7 * inch, f"Entry Number: {entry}")

        # Print the report content
        y_position = height - margin_top - 1.2*inch
        text_lines = report.split('\n')
        c.setFont("Helvetica", 12)
        
        for line in text_lines:
            # Ensure the text wraps if it's too long
            wrapped_lines = []
            while len(line) > 80:  # 80 characters per line for wrapping
                wrapped_lines.append(line[:80])
                line = line[80:]
            wrapped_lines.append(line)
            
            for wrapped_line in wrapped_lines:
                if y_position < margin_bottom:  # Avoid printing too close to the bottom
                    c.showPage()
                    y_position = height - margin_top - 1.4*inch
                    # Draw the header again
                    #c.drawImage(HEADER_IMAGE, margin_left, height - margin_top, width=2*inch, preserveAspectRatio=True, mask='auto')
                    try:
                        c.drawImage(HEADER_IMAGE, margin_left, height - margin_top -1.8*inch, width=1*inch, preserveAspectRatio=True, mask='auto')
                    except Exception as e:
                        print(f"Error loading image: {e}")
                    c.setFont("Helvetica-Bold", 14)
                    #c.drawString(margin_left + 2.1 * inch, height - margin_top + 0.2 * inch, "Your Report Header Text")
                    c.drawString(margin_left + 2.1 * inch, height - margin_top + 0.5 * inch, "Arista Surge Medical Center")
                    c.setFont("Helvetica", 12)
                    c.drawString(margin_left + 2.1 * inch, height - margin_top + 0.2 * inch, "123 Medical Way, Health City, CA 12345")
                    c.drawString(margin_left + 2.1 * inch, height - margin_top, "Phone: (123) 456-7890")
                    c.setFont("Helvetica", 12)
                c.drawString(margin_left, y_position, wrapped_line)
                y_position -= 15  # Adjust line spacing for better readability

        # Add a line separator between reports
        # y_position -= 5
        # c.line(margin_left, y_position, width - margin_right, y_position)
        c.line(margin_left, margin_bottom, width - margin_right, margin_bottom)
        y_position -= 25  # Additional spacing before the next entry

        # Draw the footer
        c.setFont("Helvetica", 8)
        c.drawString(margin_left, margin_bottom / 2, f"Page {c.getPageNumber()} - Confidential")

    c.save()
    print(f'Report for patient_id {patient_id} has been saved to {pdf_file}')

# @app.post("/print-report/")
# async def print_report_endpoint(patient_id: PatientID):
#     try:
#         await print_report(patient_id.patient_id)
#         return {"message": f"Report for patient_id {patient_id.patient_id} has been printed successfully."}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    
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

            
async def gpt_json(prompt,max_tokens):
    client = OpenAI(api_key='')
    messages = [
           {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content":  f'''{prompt}'''},
            ]
    response = client.chat.completions.create(
        model="gpt-4o-mini", #gpt-4o-mini, gpt-3.5-turbo-0125
        temperature=0,
        response_format={ "type": "json_object" },
        messages=messages
        )
    result=response.choices[0].message.content
    return result

async def task_on_EHR(reports,datetime_now,task):
    task_prompt=f"""
    You are an AI designed to assist doctors in analyzing Electronic Health Records (EHRs). You will be provided with a list of EHRs in json format for a specific patient and a task to perform on these records. The records are presented in chronological order based on their entry number. A lower entry number denotes an earlier record. You are also provided the current datatime, which you can use to compare with the Date and Time mentioned in the EHR.

    List of EHRs:
    {reports}
    
    Current Datetime:
    {datetime_now}
    
    Task to be perfomed on the EHRs:
    {task}
    
    Your output must be in json format as follows:
    output:<output of task on EHRs>
    """
    output=await gpt_json(task_prompt,1000)
    output=json.loads(output)
    #print(output)
    return output

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
        print(output)
        report_json=json.loads(output)
        patient_id_exists=True
        result=search_key_in_json(report_json,'patient id')
        if not result:
            patient_id_exists=False
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
        return (report,patient_id_exists)
    
    elif intent.lower()=='read':
        read_prompt=f'''You are an AI designed to help doctors to automate Electronic Health Records, you will be given a query by a 
         Doctor, where you are asked to read a medical record for a patient.
         The doctor wants you to first search for a patient based on a specifc attribute(like Name, Age, Surgical Procedure,etc) and the value of that attribute(like Name is Arjun, so Name is the attribute and Arjun is the value) in the Electronic Health Records, and retrive his data. After retrieval the doctor wants you to perfom a task on the retrieved record.
         
         Examples of tasks are: Retrieve Blood Pressure of the patient, Read glucose levels,etc.
         
         You output must be in json format as follows:
         value:<value of the attribute mentioned by the doctor>
         task: <task required to be perfomed on the data, must not contain the Name or value of the attribute.>
         This is the query given by the doctor: 
         {query}\n'''
        #  Name:<search attribute mentioned by the doctor>
        output=await gpt_json(read_prompt,100)
        output=json.loads(output)
        print('output json',output)
        search_attribute = output.get('value')
        task = output.get('task')
        # Perform text search in MongoDB
        search_query = {"$text": {"$search": search_attribute}}
        cursor = ehr_collection.find(search_query)
        results = []
        patient_ids = set()
        print('cursor',cursor)
        async for document in cursor:
            json_doc = ehr_helper(document)
            results.append(json_doc)
            patient_ids.add(json_doc['patient_id'])
        print('patient ids',patient_ids)
        print('patient ids length',len(patient_ids))
        print(results)
        # Check if all patient IDs are the same
        # if len(patient_ids) > 1:
        #     raise HTTPException(status_code=400, detail="Multiple patient IDs correspond to the search query")
        
        # # Only a single patient id is present
        # # Get all the documents corresponding to the same patient id
        # patient_id=list(patient_ids)[0]
        # cursor=ehr_collection.find({'patient_id': patient_id})
        # async for document in cursor:
        #     json_doc=ehr_helper(document)
        #     results.append(json_doc)
        
        output_of_task=await task_on_EHR(results,datetime.datetime.now(),task)
        #print('output_of_task',output_of_task)
        result_json=search_key_in_json(output_of_task,'output')
        print('output_json_output',result_json)
        outputs=[]
        if isinstance(result_json,list):
            for json_element in result_json:
                # output=json_to_formatted_string(json_element)
                # outputs.append(output)
                if isinstance(json_element, dict):
                    output = json_to_formatted_string(json_element)
                else:
                    output = json_element 
                outputs.append(output)
            output='\n'.join(outputs)
            print('out 1')
        else:
            # output=json_to_formatted_string(result_json)
            if isinstance(result_json, dict):
                output = json_to_formatted_string(result_json)
                print('out 2')
            else:
                output = result_json  # Pass through if it's not a dictionary
                print('out 3')
            outputs.append(output)
        #print('output',output)
        return output 
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
        
        return (report,patient_id_exists)# need to break out the actual output
    else:
        return ('No predefined intents match')
        

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
    #print('id and json report', output)
    return output

@app.post("/process_request/")
async def process_request(request: Request):
    data = await request.json()
    query = data['text'].strip()
    #print(query)
    #Intent classification here
    intent_prompt=f'''You are an AI designed to help doctors automate Electronic Health Records (EHR). You will be given a query by a doctor, which could involve creating a new medical record for a patient, reading existing medical records for a patient, updating the medical record for a patient, or deleting the medical records for a patient.

Your task is to classify the intent of the query into one of the following categories: Create, Read, Update, or Delete.

Please use the following criteria to classify the intent:

- **Create:** The query asks to create a new medical record.
  Example: "Create a new record for John Doe with the diagnosis of hypertension."

- **Read:** The query asks to retrieve or read existing medical records without making any changes.
  Example: "Retrieve the medical history for Jane Smith."

- **Update:** The query asks to modify or add or update some information. This also applies if the patient came for a follow up.
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
    if intent.lower()=='create':
        #send the report to streamlit for the user to edit
        return {"intent": intent,"create_output": output_task[0],"id_exists":output_task[1]}
    elif intent.lower()=='read':
        return {"intent": intent, "read_output":output_task}
    elif intent.lower()=='update':
        return {"intent": intent,"update_output": output_task[0],"id_exists":output_task[1]}
    else:
        return{"intent":'undefined'}

@app.post("/save_request/")
async def save_request(request: Request):
    data = await request.json()
    print(data)
    query = data['text'].strip()
    intent=data.get('intent','')
    print(query)
    print(intent)
    #Patient id will be provided-no case where it wont be there
    output_json=await extract_id_and_json_report(query)
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
        return {'message':f' Existing Patient Report has been updated and saved at {patient_id}_report.pdf'}
    else:
        print('Patient id doens\'t exist in records, creating a new report if intent is create')
        print(intent)
        if intent.lower()=='update':
            print('inside the condition')
            return {'message':'Patient id does not exist in the database'}
        
        created_record = await add_record(entry, patient_id, report)
        print(created_record)
        
        await print_report(patient_id)
        
        return {'message':f' A new Patient Report has been created and saved at {patient_id}_report.pdf'}

@app.get("/reports")
async def list_reports():
    files = os.listdir(REPORTS_DIR)
    print(files)
    return {"reports": files}

@app.get("/reports/{report_name}")
async def get_report(report_name: str):
    report_path = os.path.join(REPORTS_DIR, report_name)
    if os.path.exists(report_path):
        return FileResponse(report_path, media_type='application/pdf', filename=report_name)
    else:
        return {"error": "Report not found"}

@app.post('/process_file')
async def process_file(file: UploadFile = File(...)):
    try:
        # Read the content of the uploaded file
        content = await file.read()
        if not content:
            print("No content read from the file")
            return {"error": "No content read from the file"}

        print("File content read successfully")

        text = ""
        
        # Convert PDF pages to images
        images = convert_from_bytes(content)
        if not images:
            print("No images extracted from the PDF")
            return {"error": "No images extracted from the PDF"}
        
        print(f"{len(images)} pages extracted from the PDF")

        # Perform OCR on each image
        for page_num, image in enumerate(images):
            print(f'Processing page {page_num + 1}')
            page_text = pytesseract.image_to_string(image)
            if page_text:
                text += page_text + "\n"
                print(f"Extracted text from page {page_num + 1}: {page_text}")
            else:
                print(f"No text extracted from page {page_num + 1}")
        
        if not text:
            print("No text extracted from the entire PDF")
            return {"error": "No text extracted from the entire PDF"}
        
        print(f"Full OCR Text: {text}")
        #Some kind of report preprocessing is required, this can change with time.
        report_mod_prompt=f'''You are an AI designed to help doctors automate Electronic Health Records (EHR). You will be provided with the extracted text from a patient report. This text will contain information regarding the patient, and his medical condition and other relevant details. The text may also contain details like report headers which may include hospital name, location,etc.
        Your task is to identify the relevant medical report of the patient, and extract it.You must also search for a Patient id field in the report. In case the patient id field is not present. You must write a blank field of 'Patient id: ' , in your output report.
        Your output must be in a json format as follows:
        medical_report: <The extracted medical report>
        
        The input report:
        {text}
        '''
        output_report=await gpt_json(report_mod_prompt,300)
        output_report=json.loads(output_report)
        report = json_to_formatted_string(output_report['medical_report'])
        return {"text": report}
    except Exception as e:
        print(f"Exception: {str(e)}")
        return {"error": str(e)}

    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)