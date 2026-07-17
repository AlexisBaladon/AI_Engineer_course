import os

from dotenv import load_dotenv

load_dotenv()


HOST = "0.0.0.0"
PORT = 1236
DEBUG = (os.getenv("DEBUG", "true").lower() == "true")