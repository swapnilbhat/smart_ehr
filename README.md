# smart_ehr
An AI powered system to create, read and get recommendations from patient health records

In order to run, follow the instruction below:

## Install the requirements
`pip install -r requirements.txt`

## Frontend
`streamlit run Frontend/app.py`

## Backend
`python3 Backend/fast_api.py`

## Current Implementation
- You can create a new record, and edit it in the web interface before saving it, to ensure validity
- You can read existing records, and by entering a search query and get releavant information from the records without manually scanning through them
- You can update existing records with new information, by adding data with current timestamp to ensure record continuity and ease of access