import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://gregoryparent:your_password@localhost/portfolio_optimizer")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable unnecessary overhead
