from dotenv import load_dotenv
import os

load_dotenv()

ARIZE_SPACE_ID = os.getenv("AZIRE_SPACE_ID")
ARIZE_API_KEY = os.getenv("AZIRE_API_KEY")
ARIZE_PROJECT_NAME = os.getenv("ARIZE_PROJECT_NAME")