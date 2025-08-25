# Attendance Management System - VS Code Setup

This Flask-based attendance management system has been restructured to avoid circular import issues in VS Code.

## Project Structure

The circular import issue has been resolved by creating a separate `database.py` file:

```
├── database.py          # Database configuration (no circular imports)
├── app.py              # Flask application factory
├── models.py           # Database models
├── routes.py           # Application routes
├── email_service.py    # Email functionality
├── export_service.py   # Excel/CSV export functionality
├── run.py             # Development runner for VS Code
├── main.py            # Production runner (for Replit)
├── templates/         # HTML templates
└── static/           # CSS and JavaScript files
```

## Setup for VS Code

### 1. Install Dependencies

```bash
pip install Flask==3.0.0
pip install Flask-SQLAlchemy==3.1.1
pip install Werkzeug==3.0.1
pip install openpyxl==3.1.2
pip install email-validator==2.1.0
```

### 2. Set Environment Variables

Create a `.env` file or set these environment variables:

```bash
export SESSION_SECRET="your-secret-key-here"
export SMTP_USERNAME="your-email@gmail.com"  # Optional
export SMTP_PASSWORD="your-app-password"     # Optional
```

### 3. Run the Application

For development in VS Code:
```bash
python run.py
```

For production (Replit):
```bash
python main.py
```

## Key Changes Made

### 1. Eliminated Circular Imports

- **Before**: `app.py` ↔ `models.py` (circular import)
- **After**: `database.py` → `models.py`, `app.py` → `database.py` (no circular imports)

### 2. Database Configuration

Created `database.py`:
```python
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
```

### 3. Updated Import Statements

All files now import from `database.py` instead of `app.py`:
```python
# OLD (caused circular imports)
from app import db

# NEW (no circular imports)
from database import db
```

## Features

- **User Management**: Teacher registration and login
- **Class Management**: Create and manage classes
- **Student Management**: Add students to classes
- **Attendance Tracking**: Mark daily attendance
- **Email Notifications**: Automated absence notifications
- **Data Export**: Enhanced Excel/CSV export with statistics
- **Individual Email Settings**: Each teacher configures their own SMTP

## Email Configuration

Each teacher can configure their own email settings:
1. Go to Profile → Email Settings
2. Configure SMTP server (default: Gmail)
3. Enter your email and app password
4. Test the configuration

## Export Features

The enhanced export functionality provides:
- Students as rows, dates as columns
- Color coding (Green=Present, Red=Absent, Yellow=Late)
- Statistics (Total Present/Absent/Late, Attendance %)
- Date range filtering
- Professional formatting

## Troubleshooting

### Import Errors in VS Code

If you still see import errors:
1. Make sure you're in the correct directory
2. Check that all files are in the same folder
3. Restart VS Code Python language server (Ctrl+Shift+P → "Python: Restart Language Server")

### Database Issues

The app uses SQLite by default. The database file (`attendance.db`) will be created automatically on first run.

### Email Issues

1. For Gmail, use App Passwords (not your regular password)
2. Enable 2-factor authentication first
3. Generate an App Password in Google Account settings
4. Use the App Password in the email settings

## Development vs Production

- **Development** (`run.py`): Uses SQLite, debug mode enabled
- **Production** (`main.py`): Configured for Replit deployment

This structure ensures the application works seamlessly in both VS Code development environment and Replit production environment.