import os

from dotenv import load_dotenv


load_dotenv()

CHUNKED_DATA_PATH = "data/embedded_chunked_data.csv"
IMAGES_PATH = "data/website_images.csv"
HOST = "0.0.0.0"
PORT = 1230
DEBUG = (os.getenv("DEBUG", "true").lower() == "true")