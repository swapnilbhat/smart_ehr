from fastapi import FastAPI,Request
import uvicorn
import aiohttp
import openai
import json
import os
import re
import uuid

app=FastAPI()

health_records_directory='/home/blu/ai/smart_ehr/health_records'
health_records_lookup='/home/blu/ai/smart_ehr/health_records/ehr_lookup.json'

async def intent_classifier(query):
    prompt = f'''You are an AI designed to help doctors to automate Electronic Health Records, you will be given a query by a Doctor, where he may ask you to create a medical record for a patient, read existing medical records for a patient, update the medical record for a patient or delete the medical records for a patient.
    Your first task is to classify the intent of the query into Create, Read , Update or Delete.
    If intent of the query is Create, you need to create a Medical record of the patient based on the information provided by the doctor, and structure it into a proper format with headings and subheadings.
    Examples of headings and its subheadings:
    Heading: Patient Information ; Subheadings: Name, Age, Gender, Date of Birth, Address, Phone Number, Blood Group, etc
    Heading: Medical History
    Heading: Surgical Procedure; Subheadings: Procedure Name, Date of Surgery, Surgeon, Procedure Details, etc
    Heading: Post Operative Care
    Heading: Discharge Instructions
    Heading: Signature     
    The above list is not exhaustive and you need to add content to the relevant section based on how it appears in the query. 
    Don't mention a Heading or Subheading in the output, if its information isnt given in the query.
    Give the intent of the query in the first line, as Intent: <intent of the query> and then the medical record from a newline.
    
    After the medical record give a summary of the medical record in MAX 40 words as Summary: <summary>, mentioning key 
    details like Personal Information(Name,Age,Gender), Surgical Procedure and Medical History. Dont mention the headings in the 
    summary. This summary should contain only the key details and should be a single string on a single line.  
    This is the query given by the doctor: 
    {query}\n'''
    # Use your OpenAI API key here
    
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
        "max_tokens": 300,
    })
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, data=data) as response:
            if response.status:
                response_data = await response.json()
                intent = response_data['choices'][0]['message']['content']
                return intent
            else:
                return "Error: Failed to receive a valid response from OpenAI API"

async def extract_intent_and_content(output:str):
    # Regex to find the Intent
    # Extract Intent
    intent_match = re.search(r"^Intent: (\w+)", output, re.MULTILINE)
    if intent_match:
        intent = intent_match.group(1)
    else:
        intent = None
    if intent.lower() == 'create':
        # Extract Medical Report
        # We use the lookahead assertion (?=Summary:) to stop at the "Summary" section
        report_match = re.search(r"^Patient Information:(.+?)(?=^Summary: )", output, re.DOTALL | re.MULTILINE)
        if report_match:
            report = report_match.group(1).strip()
            if not os.path.exists(health_records_directory):
                os.makedirs(health_records_directory)
            file_id=uuid.uuid4().hex
            file_name=f'{file_id}.txt'
            file_path=os.path.join(health_records_directory,file_name)
            with open(file_path,'w') as file:
                file.write(report)
                file.write('\n')
        else:
            report = None
        
        # Extract Summary
        summary_match = re.search(r"^Summary: (.+)$", output, re.MULTILINE)
        if summary_match:
            summary = summary_match.group(1)
        else:
            summary = None
        
        if os.path.exists(health_records_lookup):
            with open(health_records_lookup,'r') as lookup_file:
                lookup_data=json.load(lookup_file)
        else:
            lookup_data={}
        
        lookup_data[file_id] = {
            "file_path": file_path,
            "summary": summary
        }
        with open(health_records_lookup,'w') as lookup_file:
            json.dump(lookup_data, lookup_file, indent=4)
            
            

    #Instead of outputting intent and patient info a message should come out like created record for patient id
    return intent,file_id,summary

@app.post("/process_request/")
async def process_request(request: Request):
    data=await request.json()
    query=data['query'].strip()
    print(query)
    #Intent classification here
    output=await intent_classifier(query)
    #Heavy regex to be employed here- separate out the intent and the following text
    intent,file_id,summary= await extract_intent_and_content(output)
    if intent.lower()=='create':
        return{"intent":f"{intent}","Generated_unique_id":f"{file_id}","Patient Summary":f"{summary}"}
    else:
        return{"intent":"Yet to be defined"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)