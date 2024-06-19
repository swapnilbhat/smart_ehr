import motor.motor_asyncio
from pymongo import TEXT

MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.health_records
ehr_collection = database.get_collection("ehr_test")

async def create_text_index():
    await ehr_collection.create_index(
        [
            ("report.Patient Information.Name", TEXT),
            ("report.Surgical Procedure", TEXT),
            ("report.Chief Complaints.Complaints", TEXT),
            ("report.Medical History.Known Conditions", TEXT)
        ],
        name="text_index"
    )

import asyncio
asyncio.run(create_text_index())
