import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "space_station_cargo_management_secret")

# Configure the database connection
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///cargo_management.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with SQLAlchemy
db.init_app(app)

# Create database tables
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import Item, Container, ItemPlacement, Log
    
    logger.info("Creating database tables...")
    db.create_all()
    logger.info("Database tables created successfully.")

# Import and register routes
from api_routes import register_api_routes

register_api_routes(app)

# Import and register web routes
from web_routes import register_web_routes

register_web_routes(app)

logger.info("Application setup complete")
