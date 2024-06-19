from fastapi import FastAPI,Request,HTTPException
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
from pymongo import TEXT

app=FastAPI()

MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.health_records
ehr_collection = database.get_collection("ehr_test")
patient_lookup=database.get_collection("patient_lookup")

# Pydantic model for EHR
class EHRModel(BaseModel):
    entry: int
    patient_id: str
    report: dict

class Query(BaseModel):
    query:str
    
# Helper function to convert BSON to JSON
def ehr_helper(ehr) -> dict:
    return {
        "id": str(ehr["_id"]),
        "entry": ehr["entry"],
        "patient_id": ehr["patient_id"],
        "report": ehr["report"]
    }
            
async def gpt_json(prompt,max_tokens):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'default-key'))
    messages = [
           {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content":  f'''{prompt}'''},
            ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        temperature=0,
        max_tokens=max_tokens,
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
#@app.get("/read_record",response_model=EHRModel)
@app.get("/read_record")
async def read_record(query: Query,response_model=dict):
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
    search_attribute = output.get('value')
    task = output.get('task')
    # Perform text search in MongoDB
    search_query = {"$text": {"$search": search_attribute}}
    cursor = ehr_collection.find(search_query)
    results = []
    patient_ids = set()
    async for document in cursor:
        json_doc = ehr_helper(document)
        results.append(json_doc)
        patient_ids.add(json_doc['patient_id'])

    # Check if all patient IDs are the same
    if len(patient_ids) > 1:
        raise HTTPException(status_code=400, detail="Multiple patient IDs correspond to the search query")
    
    # Only a single patient id is present
    # Get all the documents corresponding to the same patient id
    patient_id=list(patient_ids)[0]
    cursor=ehr_collection.find({'patient_id': patient_id})
    async for document in cursor:
        json_doc=ehr_helper(document)
        results.append(json_doc)
    
    output_of_task=await task_on_EHR(results,datetime.datetime.now(),task)
    
    return output_of_task
    #return {"Search Attribute": search_attribute, "Task": task, "Patient id": patient_id,"Results":results}
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    


# read_prompt=f'''You are an AI designed to help doctors to automate Electronic Health Records, you will be given a query by a 
#          Doctor, where you are asked to read a medical record for a patient.
#          The doctor wants you to first search for a patient based on a specifc attribute(like Name, Age, Surgical Procedure,etc) and the value of that attribute(like Name is Arjun, so Name is the attribute and Arjun is the value) in the Electronic Health Records, and retrive his data. After retrieval the doctor wants you to perfom a task on the retrieved record.
#          Examples of tasks are: Retrieve Blood Pressure of the patient, Read glucose levels,etc.
#          The task value needs to be extracted from the task, refer the examples:
#          1)
#          Task: Retrieve Blood Pressure of the patient
#          Task value: Blood Pressure
#          2)
#          Task:Read glucose levels
#          Task value: glucose level
         
#          You output must be in json format as follows:
#          value:<value of the attribute mentioned by the doctor>
#          task value : <task value to be extracted from the task>
#          This is the query given by the doctor: 
#          {query}\n'''