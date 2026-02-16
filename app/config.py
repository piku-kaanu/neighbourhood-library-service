import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/library_db"
    )
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-env")

settings = Settings()
