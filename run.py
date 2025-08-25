"""
Development runner for VS Code
This file provides an alternative way to run the application in VS Code
"""
import os
from app import app

if __name__ == "__main__":
    # Set development environment variables if not set
    if not os.environ.get("SESSION_SECRET"):
        os.environ["SESSION_SECRET"] = "dev-secret-key-change-in-production"
    
    # Run the application
    app.run(host="0.0.0.0", port=5000, debug=True)