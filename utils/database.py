from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB client and database
client = None
db = None

def init_db():
    """Initialize MongoDB connection"""
    global client, db

    try:
        mongodb_uri = os.getenv('MONGODB_URI')
        db_name = os.getenv('MONGODB_DB_NAME', 'citycare')

        if not mongodb_uri:
            print("❌ Error: MONGODB_URI not found in .env file")
            return False

        # Create MongoDB client
        # For MongoDB Atlas, SSL/TLS is handled automatically by the connection string
        client = MongoClient(
            mongodb_uri,
            serverSelectionTimeoutMS=5000
        )

        # Test connection
        client.admin.command('ping')

        # Get database
        db = client[db_name]

        # Create indexes
        create_indexes()

        print(f"✅ Connected to MongoDB: {db_name}")
        return True

    except ConnectionFailure as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def get_db():
    """Get database instance"""
    global db
    if db is None:
        init_db()
    return db

def create_indexes():
    """Create database indexes for better performance"""
    global db

    try:
        # Users collection indexes
        db.users.create_index('email', unique=True)
        db.users.create_index('phone')
        db.users.create_index('role')

        # Complaints collection indexes
        db.complaints.create_index('user_id')
        db.complaints.create_index('status')
        db.complaints.create_index('category')
        db.complaints.create_index('created_at')

        print("✅ Database indexes created")
    except Exception as e:
        print(f"⚠️  Warning: Could not create indexes: {e}")

def close_db():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("✅ MongoDB connection closed")