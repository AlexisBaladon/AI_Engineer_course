import os

from dotenv import load_dotenv


load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = os.getenv("PORT", 1232)
DEBUG = os.getenv("DEBUG", True)

RETRIEVAL_HOST = os.getenv("RETRIEVAL_HOST", "localhost")
RETRIEVAL_PORT = os.getenv("RETRIEVAL_PORT", 1230)

RANKING_HOST = os.getenv("RANKING_HOST", "localhost")
RANKING_PORT = os.getenv("RANKING_PORT", 1233)

GENERATION_HOST = os.getenv("GENERATION_HOST", "localhost")
GENERATION_PORT = os.getenv("GENERATION_PORT", 1231)

HOOK_HOST = os.getenv("HOOK_HOST", "localhost")
HOOK_PORT = os.getenv("HOOK_PORT", 1235)