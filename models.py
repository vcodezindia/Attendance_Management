from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Email settings
    smtp_email = db.Column(db.String(120), nullable=True)  # Email for sending notifications
    smtp_password = db.Column(db.Text, nullable=True)  # App password for SMTP
    smtp_server = db.Column(db.String(100), default='smtp.gmail.com')
    smtp_port = db.Column(db.Integer, default=587)
    email_notifications_enabled = db.Column(db.Boolean, default=True)
    
    # Relationships
    classes = db.relationship('Class', backref='teacher', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def set_smtp_password(self, smtp_password):
        """Store SMTP password (in production, use proper encryption)"""
        if smtp_password:
            # For demo purposes, store in plain text
            # In production, use proper encryption/decryption
            self.smtp_password = smtp_password
        else:
            self.smtp_password = None
    
    def get_smtp_password(self):
        """Return the SMTP password"""
        return self.smtp_password
    
    def has_email_config(self):
        """Check if teacher has configured email settings"""
        return bool(self.smtp_email and self.smtp_password)
    
    def __repr__(self):
        return f'<Teacher {self.email}>'

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    students = db.relationship('Student', backref='class_ref', lazy=True, cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', backref='class_ref', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Class {self.name}>'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    student_id = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.name}>'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Present, Absent, Late
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_sent = db.Column(db.Boolean, default=False)  # Track if absence email was sent
    
    # Composite unique constraint to prevent duplicate entries
    __table_args__ = (db.UniqueConstraint('student_id', 'class_id', 'date', name='unique_attendance'),)
    
    def __repr__(self):
        return f'<Attendance {self.student.name} - {self.date} - {self.status}>'
