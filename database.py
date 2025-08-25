"""
Database configuration and initialization
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Create the database instance
db = SQLAlchemy(model_class=Base)