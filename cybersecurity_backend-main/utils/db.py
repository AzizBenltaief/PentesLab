from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "pentestlab")

if not MONGODB_URL:
    print("Warning: MONGODB_URL not set. Using default: mongodb://localhost:27017")
    MONGODB_URL = "mongodb://localhost:27017"

# MongoDB client and database
client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
users_collection = db["users"]
projects_collection = db["projects"]
scan_results_collection = db["scan_results"]
audit_logs_collection = db["audit_logs"]
user_feedback_collection = db["user_feedback"]
vulnerability_coverage_collection = db["vulnerability_coverage"]
scan_chats_collection = db["scan_chats"]

async def init_db():
    """Initialize database indexes for performance."""
    # Create indexes for users
    await users_collection.create_index("username", unique=True)
    await users_collection.create_index("email", unique=True)
    
    # Create indexes for projects
    await projects_collection.create_index("owner_id")
    await projects_collection.create_index("created_at")
    
    # Create indexes for scan results
    await scan_results_collection.create_index("project_id")
    await scan_results_collection.create_index("target_url")
    await scan_results_collection.create_index("created_at")
    
    # Create indexes for audit logs
    await audit_logs_collection.create_index("user_id")
    await audit_logs_collection.create_index("timestamp")
    await audit_logs_collection.create_index("username")
    
    # Create indexes for user feedback
    await user_feedback_collection.create_index("user_id")
    await user_feedback_collection.create_index("timestamp")
    await user_feedback_collection.create_index("category")
    
    # Create indexes for vulnerability coverage
    await vulnerability_coverage_collection.create_index("scan_id")
    await vulnerability_coverage_collection.create_index("timestamp")

    # Create indexes for scan chats
    await scan_chats_collection.create_index("scan_id")
    await scan_chats_collection.create_index("user_id")

def get_db():
    """Return database instance."""
    return db
