import os

from dotenv import load_dotenv


load_dotenv()

HOST = "0.0.0.0"
PORT = 1231
DEBUG = (os.getenv("DEBUG", "true").lower() == "true")

TOOLS_IMAGES_DIR = os.getenv("TOOLS_IMAGE_DIR", "generated_boards")

BACKEND_PREFIX = os.getenv("FRONTEND_PREFIX", "http")
BACKEND_HOST = os.getenv("VITE_BACKEND_HOST", "localhost")
BACKEND_PORT = os.getenv("VITE_BACKEND_PORT", 1235)
BACKEND_ORIGIN = f"{BACKEND_PREFIX}://{BACKEND_HOST}"
if not (BACKEND_PREFIX == "https" and BACKEND_PORT == 443):
    BACKEND_ORIGIN += f":{BACKEND_PORT}"