import os
from datetime import datetime
from pymongo import MongoClient, errors

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "ai-campus-admin-agent")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    short_term_col = db["short_term_memory"]
    long_term_col = db["long_term_memory"]
except errors.PyMongoError as e:
    print(f"[MongoDB Connection Error] {e}")
    client, db, short_term_col, long_term_col = None, None, None, None


# ================= SHORT-TERM MEMORY ==================
def save_short_term_memory(user_id: str, thread_id: str, message: str, role: str = "user"):
    """Save a message to short-term memory for a specific thread."""
    if not short_term_col:
        return
    try:
        short_term_col.insert_one({
            "user_id": user_id,
            "thread_id": thread_id,
            "role": role,
            "message": message,
            "timestamp": datetime.utcnow()
        })
    except errors.PyMongoError as e:
        print(f"[MongoDB Error] save_short_term_memory: {e}")

def get_short_term_memory(user_id: str, thread_id: str, limit: int = 10):
    """Retrieve last N messages from short-term memory for a thread."""
    if not short_term_col:
        return []
    try:
        docs = short_term_col.find(
            {"user_id": user_id, "thread_id": thread_id}
        ).sort("timestamp", -1).limit(limit)
        return list(docs)[::-1]
    except errors.PyMongoError as e:
        print(f"[MongoDB Error] get_short_term_memory: {e}")
        return []


def clear_short_term_memory(user_id: str, thread_id: str):
    """Clear short-term memory for a specific thread."""
    if not short_term_col:
        return
    try:
        short_term_col.delete_many({"user_id": user_id, "thread_id": thread_id})
    except errors.PyMongoError as e:
        print(f"[MongoDB Error] clear_short_term_memory: {e}")


# ================= LONG-TERM MEMORY ==================
def save_long_term_memory(user_id: str, summary: str, tags: list = None):
    """Save long-term memory as summaries or key facts."""
    if not long_term_col:
        return
    try:
        long_term_col.insert_one({
            "user_id": user_id,
            "summary": summary,
            "tags": tags or [],
            "timestamp": datetime.utcnow()
        })
    except errors.PyMongoError as e:
        print(f"[MongoDB Error] save_long_term_memory: {e}")


def get_long_term_memory(user_id: str, limit: int = 20):
    """Retrieve long-term memory entries."""
    if not long_term_col:
        return []
    try:
        docs = long_term_col.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        return list(docs)[::-1]
    except errors.PyMongoError as e:
        print(f"[MongoDB Error] get_long_term_memory: {e}")
        return []


def clear_long_term_memory(user_id: str):
    """Clear all long-term memory for a user."""
    if not long_term_col:
        return
    try:
        long_term_col.delete_many({"user_id": user_id})
    except errors.PyMongoError as e:
        print(f"[MongoDB Error] clear_long_term_memory: {e}")
