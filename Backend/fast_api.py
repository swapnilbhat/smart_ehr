from fastapi import FastAPI,Request
import uvicorn
import spacy
import aiohttp
import openai
import json
import os
app=FastAPI()
nlp = spacy.load("en_core_web_sm")

async def intent_classifier(query):
    # prompt = f"Classify the intent of the following user query: '{query}'\n\nPossible intents are Create, Read, Update, Delete.Identify the intent which matches the query and give the intent as output."
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
    This is the query given by the doctor: 
    {query}\n'''
    # Use your OpenAI API key here
    
    openai_api_key = os.getenv('OPENAI_API_KEY', 'default_api_key_if_not_set')

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
        "temperature": 0.1,
        "max_tokens": 300,
    })
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, data=data) as response:
            if response.status:
                response_data = await response.json()
                #intent = response_data['choices'][0]['text'].strip()
                intent = response_data['choices'][0]['message']['content']
                return intent
            else:
                return "Error: Failed to receive a valid response from OpenAI API"


@app.post("/process_request/")
async def process_request(request: Request):
    data=await request.json()
    query=data['query'].strip()
    print(query)
    #Intent classification here
    intent=await intent_classifier(query)
    print(intent)
    #NLP action here
    return{"message":"query recieved"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)