import os

from dotenv import load_dotenv


load_dotenv()

# Main server
HOST = "0.0.0.0"
PORT = 1232
DEBUG = (os.getenv("DEBUG", "true").lower() == "true")

# Server connections
RETRIEVAL_HOST = os.getenv("RETRIEVAL_HOST", "localhost")
RETRIEVAL_PORT = os.getenv("RETRIEVAL_PORT", 1230)

RANKING_HOST = os.getenv("RANKING_HOST", "localhost")
RANKING_PORT = os.getenv("RANKING_PORT", 1233)

GENERATION_HOST = os.getenv("GENERATION_HOST", "localhost")
GENERATION_PORT = os.getenv("GENERATION_PORT", 1231)

HOOK_HOST = os.getenv("HOOK_HOST", "localhost")
HOOK_PORT = os.getenv("HOOK_PORT", 1235)

# Observability
ARIZE_SPACE_ID = os.getenv("AZIRE_SPACE_ID")
ARIZE_API_KEY = os.getenv("AZIRE_API_KEY")
ARIZE_PROJECT_NAME = os.getenv("ARIZE_PROJECT_NAME")