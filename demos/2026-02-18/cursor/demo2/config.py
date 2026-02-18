"""Flask application configuration."""

import os

# Use absolute path so the database is always in the same place
# regardless of which directory you run the app from
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "instance", "users.db")


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RESTFUL_JSON = {"ensure_ascii": False}
    # Pagination defaults
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
