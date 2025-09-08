from dotenv import load_dotenv
import os

load_dotenv()

YOUTUBE_DATA_API = os.getenv("YOUTUBE_DATA_API")
DATABASE_URL = os.getenv("DATABASE_URL")