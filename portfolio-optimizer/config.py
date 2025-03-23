import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///test.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable unnecessary overhead
