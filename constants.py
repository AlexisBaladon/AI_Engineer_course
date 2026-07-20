import os

from dotenv import load_dotenv


load_dotenv()

HOST = "0.0.0.0"
PORT = 1235
DEBUG = (os.getenv("DEBUG", "true").lower() == "true")

FRONTEND_PREFIX = os.getenv("FRONTEND_PREFIX", "http")
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "localhost")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", 5173))

FRONTEND_ORIGIN = f"{FRONTEND_PREFIX}://{FRONTEND_HOST}"
if not (FRONTEND_PREFIX == "https" and FRONTEND_PORT == 443):
    FRONTEND_ORIGIN += f":{FRONTEND_PORT}"

ADMIN_USER_USERNAME = os.getenv("ADMIN_USER_USERNAME", "root")
ADMIN_USER_PASSWORD = os.getenv("ADMIN_USER_PASSWORD", "123")
ENCRYPTION_SECRET_KEY = os.getenv("ENCRYPTION_SECRET_KEY", "123")

USER_ROLE = os.getenv("USER_ROLE", "user")
ADMIN_ROLE = os.getenv("ADMIN_ROLE", "admin")

CHUNKED_DATA_PATH = "./ingestion/embedded_chunked_data.csv"
IMAGES_PATH = "./ingestion/website_images.csv"

TOOLS_IMAGES_DIR = os.getenv("TOOLS_IMAGE_DIR", "generated_boards")

# This assumes frontend and backend are served using the same method (http vs https)
BACKEND_PREFIX = FRONTEND_PREFIX
BACKEND_HOST = os.getenv("VITE_BACKEND_HOST", "localhost")
BACKEND_PORT = os.getenv("VITE_BACKEND_PORT", 1235)
BACKEND_ORIGIN = f"{BACKEND_PREFIX}://{BACKEND_HOST}"
if not (BACKEND_PREFIX == "https" and BACKEND_PORT == 443):
    BACKEND_ORIGIN += f":{BACKEND_PORT}"