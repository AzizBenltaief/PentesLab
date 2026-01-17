"""Clear all scan results from MongoDB"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def clear_scans():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.pentestlab
    
    result = await db.scan_results.delete_many({})
    print(f"Cleared {result.deleted_count} scan results from MongoDB")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(clear_scans())
