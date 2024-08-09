# smart_ehr
An AI powered system to create, read and get recommendations from patient health records

In order to run, follow the instruction below:

## Install the requirements(Inside virtual env and frontend)
- Inside python virtual environment- Running the Backend
`pip install fastapi uvicorn openai aiohttp motor reportlab pdf2image pytesseract`
- Inside react frontend directory
`npm install`

## Installations for OCR
- Poppler for Windows
- Tesseract for Windows

## Running the Frontend
- `cd react_frontend`
- `npm run dev`

## Backend-Running on Windows
`python fast_api_backend/fast_api.py`

## MongoDB setup for winows
Follow the guide:
https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-windows/

## Current Implementation
- You can create a new record, and edit it in the web interface before saving it, to ensure validity
- You can read existing records, and by entering a search query and get releavant information from the records without manually scanning through them
- You can update existing records with new information, by adding data with current timestamp to ensure record continuity and ease of access