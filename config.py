# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------
# Base directory & env loader
# -------------------------------------------------
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / ".env")   # auto-load .env file

def env(key, default=None):
    return os.environ.get(key, default)

# -------------------------------------------------
# Config
# -------------------------------------------------
class Config:
    # -------------------------
    # Flask / App
    # -------------------------
    SECRET_KEY = env("SECRET_KEY", "change-me-to-a-secure-value")
    DEBUG = env("FLASK_DEBUG", "0") == "1"
    TESTING = env("FLASK_TESTING", "0") == "1"
    SITE_NAME = "Abhijeet College"

    # -------------------------
    # Database (separate values)
    # -------------------------
    DB_ENGINE = env("DB_ENGINE", "mysql+pymysql")
    DB_USER = env("DB_USER", "root")
    DB_PASSWORD = env("DB_PASSWORD", "")
    DB_HOST = env("DB_HOST", "127.0.0.1")
    DB_PORT = env("DB_PORT", "3306")
    DB_NAME = env("DB_NAME", "forumdb")

    SQLALCHEMY_DATABASE_URI = (
        f"{DB_ENGINE}://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

