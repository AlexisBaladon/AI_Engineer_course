import os

from dotenv import load_dotenv


load_dotenv()

HOST = "0.0.0.0"
PORT = 1235
DEBUG = (os.getenv("DEBUG", "true").lower() == "true")

FRONTEND_HOST = os.getenv("FRONTEND_HOST", "localhost")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", 5173)

ADMIN_USER_USERNAME = os.getenv("ADMIN_USER_USERNAME", "root")
ADMIN_USER_PASSWORD = os.getenv("ADMIN_USER_PASSWORD", "123")
ENCRYPTION_SECRET_KEY = os.getenv("ENCRYPTION_SECRET_KEY", "123")

USER_ROLE = os.getenv("USER_ROLE", "user")
ADMIN_ROLE = os.getenv("ADMIN_ROLE", "admin")

CHUNKED_DATA_PATH = "./ingestion/embedded_chunked_data.csv"
IMAGES_PATH = "./ingestion/website_images.csv"
