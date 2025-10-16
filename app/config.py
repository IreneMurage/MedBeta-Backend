import os
from dotenv import load_dotenv

# loading environmental variables

load_dotenv()
# print("ENV Credentials")
# print(os.getenv("DATABASE_URL"))

class Config:
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    
