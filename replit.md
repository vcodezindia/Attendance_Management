# Overview

This is a Flask-based Attendance Management System designed for teachers to manage their classes, students, and track attendance records. The application provides a web interface for teachers to register, create classes, add students, mark attendance, view attendance history, and export attendance data. It includes individual teacher email settings for automated absence notifications and comprehensive reporting features with enhanced export functionality.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Flask web framework with Python
- **Database**: SQLite with SQLAlchemy ORM for data persistence
- **Authentication**: Session-based authentication with password hashing using Werkzeug security utilities
- **Blueprint Structure**: Modular route organization using Flask blueprints

## Data Models
- **Teacher**: Stores teacher credentials and profile information
- **Class**: Represents academic classes with subject information
- **Student**: Student records linked to specific classes
- **Attendance**: Daily attendance records linking students to classes with date stamps

## Frontend Architecture
- **Template Engine**: Jinja2 templating with Bootstrap 5 dark theme
- **Responsive Design**: Mobile-first approach using Bootstrap grid system
- **Client-side**: Vanilla JavaScript for form enhancements, tooltips, and auto-save functionality
- **UI Components**: Modern card-based layout with intuitive navigation

## Key Features
- **User Management**: Teacher registration and login system with individual profiles
- **Class Management**: Create and manage multiple classes with subjects
- **Student Management**: Add students individually or via bulk import from Excel/CSV files
- **Bulk Student Import**: Upload Excel (.xlsx) or CSV files with flexible column mapping and duplicate handling
- **Attendance Tracking**: Daily attendance marking with date selection
- **Historical Reporting**: Filterable attendance history with date ranges
- **Enhanced Data Export**: Excel and CSV export with students as rows, dates as columns, statistics, and color coding
- **Individual Email Settings**: Each teacher can configure their own SMTP credentials
- **Smart Email Notifications**: One email per student per day with professional content asking for absence justification
- **Email Testing**: Built-in test email functionality to verify SMTP configuration

## Security Implementation
- Password hashing with Werkzeug security functions
- Session-based authentication with login requirements
- Input validation and CSRF protection through form handling

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework
- **Flask-SQLAlchemy**: Database ORM integration
- **Werkzeug**: Security utilities for password hashing

## Frontend Dependencies
- **Bootstrap 5**: CSS framework with dark theme from Replit CDN
- **Bootstrap Icons**: Icon library for UI elements
- **Custom CSS/JS**: Enhanced styling and client-side functionality

## Email Service Integration
- **SMTP**: Email delivery system for absence notifications
- **Gmail SMTP**: Default configuration for sending emails through Gmail

## Export Service Dependencies
- **openpyxl**: Excel file generation for attendance reports
- **csv**: Built-in Python module for CSV export functionality

## Environment Configuration
- **SMTP_SERVER**: Email server configuration (defaults to Gmail)
- **SMTP_PORT**: Email server port (default: 587)
- **SMTP_USERNAME**: Email authentication username
- **SMTP_PASSWORD**: Email authentication password (app-specific password recommended)
- **SESSION_SECRET**: Flask session security key

## Database Storage
- **SQLite**: Local file-based database (attendance.db)
- **File Storage**: Temporary files for export generation