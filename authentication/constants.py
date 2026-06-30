import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_USER_USERNAME = os.getenv("ADMIN_USER_USERNAME", "root")
ADMIN_USER_PASSWORD = os.getenv("ADMIN_USER_PASSWORD", "123")
ENCRYPTION_SECRET_KEY = os.getenv("ENCRYPTION_SECRET_KEY", "123")

HOST = "0.0.0.0"
PORT = 1234
DEBUG = True

HOOK_HOST = os.getenv("HOOK_HOST", "localhost")
HOOK_PORT = os.getenv("HOOK_PORT", 1235)