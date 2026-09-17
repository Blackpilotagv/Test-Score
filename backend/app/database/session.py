import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from app.core.config import settings

# Attempt MongoDB Atlas connection first, fallback to local MongoDB instance
mongo_connected = False
try:
    mongo_client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=3000, tlsAllowInvalidCertificates=True)
    mongo_client.admin.command('ping')
    mongo_connected = True
    print("[DB INFO] Successfully connected to MongoDB Atlas.")
except Exception as atlas_err:
    print(f"[DB WARNING] Could not connect to MongoDB Atlas ({atlas_err}). Trying local MongoDB...")
    try:
        mongo_client = MongoClient("mongodb://127.0.0.1:27017", serverSelectionTimeoutMS=2000)
        mongo_client.admin.command('ping')
        mongo_connected = True
        print("[DB INFO] Successfully connected to local MongoDB (127.0.0.1:27017).")
    except Exception as local_err:
        print("[DB ERROR] Failed to connect to MongoDB Atlas and Local MongoDB!")
        print(" -> To resolve Atlas error: Whitelist your IP in MongoDB Atlas Security -> Network Access -> Add IP Address (0.0.0.0/0).")
        mongo_client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=3000, tlsAllowInvalidCertificates=True)

mongo_db = mongo_client[settings.MONGODB_DB_NAME]

def get_db():
    """FastAPI Dependency for returning MongoDB database instance."""
    return mongo_db

def get_mongo_db():
    """Helper function to return MongoDB database instance directly."""
    return mongo_db

def get_next_sequence(db, sequence_name: str) -> int:
    """Atomic counter for auto-incrementing integer document IDs."""
    ret = db.counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=pymongo.ReturnDocument.AFTER
    )
    return ret["seq"]

