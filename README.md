# smart_ehr
An AI powered system to create, read and get recommendations from patient health records

In order to run, follow the instruction below:

## Install the requirements
`pip install -r requirements.txt`

## Frontend
`streamlit run Frontend/app.py`

## Backend
`python3 Backend/fast_api.py`

## Steps to run the docker container- commands should be run in ubuntu terminal:
- `docker load < smart_ehr.tar`
- Verify that the image is created, run `docker images`
- `sudo docker run -d -p 8501:8501 -p 8000:8000 --name smart_ehr_app smart_ehr`
- Open `localhost:8501` on your browser to see the streamlit interface

## Check the reports inside the docker container- commands should be run in ubuntu terminal:
- `docker exec -it smart_ehr_app bash` opens up the terminal inside the docker
- `cd health_records`
- Use `ls` and `cat` commands to look into the file content

## Current Implementation
- You can create a new record, and edit it in the web interface before saving it, to ensure validity
- You can read existing records, and by entering a search query and get releavant information from the records without manually scanning through them
- You can update existing records with new information, by adding data with current timestamp to ensure record continuity and ease of access