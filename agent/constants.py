import os

from dotenv import load_dotenv


load_dotenv()

HOST = "0.0.0.0"
PORT = 1231
DEBUG = (os.getenv("DEBUG", "true").lower() == "true")

TOOLS_IMAGES_DIR = os.getenv("TOOLS_IMAGE_DIR", "generated_boards")

IMAGE_STORAGE_PREFIX = os.getenv("IMAGE_STORAGE_PREFIX", "http")
IMAGE_STORAGE_HOST = os.getenv("IMAGE_STORAGE_HOST", "localhost")
IMAGE_STORAGE_PORT = os.getenv("IMAGE_STORAGE_PORT", 1235)

IMAGE_STORAGE_ORIGIN = f"{IMAGE_STORAGE_PREFIX}://{IMAGE_STORAGE_HOST}"
if not (IMAGE_STORAGE_PREFIX == "https" and IMAGE_STORAGE_PORT == 443):
    IMAGE_STORAGE_ORIGIN += f":{IMAGE_STORAGE_PORT}"