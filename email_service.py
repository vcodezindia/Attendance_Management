import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_absence_notification(student, class_obj, attendance_date, teacher):
    """
    Send email notification to absent student with improved content
    """
    try:
        # Check if teacher has email notifications enabled and configured
        if not teacher.email_notifications_enabled or not teacher.has_email_config():
            logging.warning(f"Email notifications not configured for teacher {teacher.email}")
            return False
        
        # SMTP configuration from teacher's settings
        smtp_server = teacher.smtp_server or 'smtp.gmail.com'
        smtp_port = teacher.smtp_port or 587
        smtp_username = teacher.smtp_email
        smtp_password = teacher.get_smtp_password()
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = student.email
        msg['Subject'] = f'Absence Notification - {class_obj.name} - {attendance_date.strftime("%B %d, %Y")}'
        
        # Enhanced email body
        body = f"""
Dear {student.name},

This is an automated notification to inform you that you were marked absent in the following class:

📚 Intership Details:
   • Session: {class_obj.name}
   • Domain: {class_obj.subject}
   • Date: {attendance_date.strftime('%A, %B %d, %Y')}
   • Team Lead: {teacher.name}

📝 Action Required:
Please provide a reason for your absence by replying to this email.

⚠️ Important Note:
If you have already informed your team lead about this absence, please ignore this email.

If you believe this absence notification is incorrect, please contact your Team Lead immediately to resolve the issue.

Best regards,
{teacher.name}
📧 {teacher.email}

---
This is an automated message from the Attendance Management System.
Please do not reply to this email unless providing absence justification.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, student.email, text)
        server.quit()
        
        logging.info(f"Absence notification sent to {student.email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send email to {student.email}: {str(e)}")
        return False

def send_test_email(recipient_email, teacher):
    """
    Send a test email to verify SMTP configuration
    """
    try:
        # Check if teacher has email configuration
        if not teacher.has_email_config():
            return False, "Email settings not configured. Please configure your SMTP settings in your profile."
        
        # SMTP configuration from teacher's settings
        smtp_server = teacher.smtp_server or 'smtp.gmail.com'
        smtp_port = teacher.smtp_port or 587
        smtp_username = teacher.smtp_email
        smtp_password = teacher.get_smtp_password()
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = recipient_email
        msg['Subject'] = 'Test Email - Attendance Management System'
        
        # Test email body
        body = f"""
Dear User,

This is a test email from the Attendance Management System.

✅ Email Configuration Status: Working correctly!

📧 SMTP Server: {smtp_server}
📡 Port: {smtp_port}
👤 From: {smtp_username}
🏫 Teacher: {teacher.name}
📅 Test Date: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}

If you received this email, your email configuration is working properly and absence notifications will be sent to students automatically.

Best regards,
Attendance Management System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, recipient_email, text)
        server.quit()
        
        logging.info(f"Test email sent successfully to {recipient_email}")
        return True, "Test email sent successfully!"
        
    except Exception as e:
        error_msg = f"Failed to send test email: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def test_email_configuration():
    """
    Test email configuration
    """
    try:
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not smtp_username or not smtp_password:
            return False, "SMTP credentials not configured"
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.quit()
        
        return True, "Email configuration is valid"
        
    except Exception as e:
        return False, f"Email configuration error: {str(e)}"
