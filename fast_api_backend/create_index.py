import motor.motor_asyncio
from pymongo import TEXT

MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.health_records
ehr_collection = database.get_collection("investigations")

async def create_text_index():
    await ehr_collection.create_index(
        { "$**": "text" }
    )

import asyncio
asyncio.run(create_text_index())
print('done')