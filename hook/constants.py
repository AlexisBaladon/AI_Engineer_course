import os

from dotenv import load_dotenv


load_dotenv()

HOST = "0.0.0.0"
PORT = 1235
DEBUG = (os.getenv("DEBUG", "true").lower() == "true")

FRONTEND_HOST = os.getenv("FRONTEND_HOST", "localhost")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", 5173)

ORCHESTRATION_HOST = os.getenv("ORCHESTRATION_HOST", "localhost")
ORCHESTRATION_PORT = os.getenv("ORCHESTRATION_PORT", 1232)

AUTHENTICATION_HOST = os.getenv("AUTHENTICATION_HOST", "localhost")
AUTHENTICATION_PORT = os.getenv("AUTHENTICATION_PORT", 1234)

USER_ROLE = os.getenv("USER_ROLE", "user")
ADMIN_ROLE = os.getenv("ADMIN_ROLE", "admin")