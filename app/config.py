import os
from dotenv import load_dotenv

# loading environmental variables

load_dotenv()
# print("ENV Credentials")
# print(os.getenv("DATABASE_URL"))

class Config:
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS=False

    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"options": "-4"},  # Force IPv4 connections
        "pool_pre_ping": True,       # Detect broken connections
        "pool_recycle": 300,         # Recycle connections every 5 minutes
        "pool_size": 5,              # Max active connections per process
        "max_overflow": 2            # Allow 2 temporary connections above pool_size
    }
