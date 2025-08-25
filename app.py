import os
import logging
from flask import Flask
from database import db

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///attendance.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions with app
    db.init_app(app)
    
    # Import models and routes
    from models import Teacher, Class, Student, Attendance
    from routes import main_bp
    
    # Register blueprints
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logging.info("Database tables created successfully")
    
    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
