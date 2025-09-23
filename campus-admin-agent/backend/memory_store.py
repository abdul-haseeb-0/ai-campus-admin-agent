# memory_store.py
import os
from datetime import datetime
from pymongo import MongoClient

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "campus_assistant")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
short_term_col = db["short_term_memory"]
long_term_col = db["long_term_memory"]


# ================= SHORT-TERM MEMORY ==================
def save_short_term_memory(user_id: str, thread_id: str, message: str, role: str = "user"):
    """Save a single message to short-term memory (per-thread)."""
    short_term_col.insert_one({
        "user_id": user_id,
        "thread_id": thread_id,
        "role": role,
        "message": message,
        "timestamp": datetime.utcnow()
    })


def get_short_term_memory(user_id: str, thread_id: str, limit: int = 10):
    """Retrieve last N messages from short-term memory for a thread."""
    return list(
        short_term_col.find(
            {"user_id": user_id, "thread_id": thread_id}
        ).sort("timestamp", -1).limit(limit)
    )[::-1]  # reverse for chronological order


def clear_short_term_memory(user_id: str, thread_id: str):
    """Clear short-term memory for a specific thread."""
    short_term_col.delete_many({"user_id": user_id, "thread_id": thread_id})


# ================= LONG-TERM MEMORY ==================
def save_long_term_memory(user_id: str, summary: str, tags: list = None):
    """Save long-term memory as summaries or key facts."""
    long_term_col.insert_one({
        "user_id": user_id,
        "summary": summary,
        "tags": tags or [],
        "timestamp": datetime.utcnow()
    })


def get_long_term_memory(user_id: str, limit: int = 20):
    """Retrieve long-term memory entries."""
    return list(
        long_term_col.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    )[::-1]


def clear_long_term_memory(user_id: str):
    """Clear all long-term memory for a user."""
    long_term_col.delete_many({"user_id": user_id})
