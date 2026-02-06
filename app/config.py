import os
from dotenv import load_dotenv

load_dotenv()

MODEL_URL = os.getenv("MODEL_URL", "http://localhost:8001")
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "")
