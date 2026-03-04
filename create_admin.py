"""
Run this ONCE on your server to create the admin account.
Command: python create_admin.py

Admin Credentials:
  Email    : admin@citycare.gov
  Password : CC@Admin#7394
"""

import bcrypt
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "your-mongo-uri-here")

client = MongoClient(MONGO_URI)
db = client["citycare"]

email    = "admin@citycare.gov"
password = "CC@Admin#7394"

# Check if admin already exists
existing = db.users.find_one({"email": email})
if existing:
    print("⚠️  Admin already exists!")
    client.close()
    exit()

hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

admin = {
    "name"      : "CityCare Admin",
    "email"     : email,
    "phone"     : "9999999999",
    "password"  : hashed,
    "role"      : "admin",
    "created_at": datetime.utcnow(),
}

result = db.users.insert_one(admin)

print("✅ Admin created successfully!")
print(f"   ID       : {result.inserted_id}")
print(f"   Email    : {email}")
print(f"   Password : {password}")
print(f"   Role     : admin")

client.close()