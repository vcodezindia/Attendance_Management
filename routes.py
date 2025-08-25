import os
import tempfile
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import db
from models import Teacher, Class, Student, Attendance
from email_service import send_absence_notification, send_test_email
from export_service import export_to_excel, export_to_csv
try:
    from bulk_import_service import process_bulk_import, allowed_file
    BULK_IMPORT_AVAILABLE = True
except ImportError:
    logging.warning("Bulk import service not available - pandas required")
    BULK_IMPORT_AVAILABLE = False
    
    # Fallback functions
    def process_bulk_import(*args, **kwargs):
        return {'success': False, 'errors': ['Pandas is required for bulk import functionality']}
    
    def allowed_file(filename):
        return False
import logging

main_bp = Blueprint('main', __name__)

# Helper function to check if user is logged in
def require_login():
    if 'teacher_id' not in session:
        return False
    return True

@main_bp.route('/')
def index():
    if require_login():
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        teacher = Teacher.query.filter_by(email=email).first()
        
        if teacher and teacher.check_password(password):
            session['teacher_id'] = teacher.id
            session['teacher_name'] = teacher.name
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        # Check if teacher already exists
        existing_teacher = Teacher.query.filter_by(email=email).first()
        if existing_teacher:
            flash('Email already registered!', 'error')
            return render_template('register.html')
        
        # Create new teacher
        teacher = Teacher(name=name, email=email)
        teacher.set_password(password)
        
        db.session.add(teacher)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/dashboard')
def dashboard():
    if not require_login():
        return redirect(url_for('main.login'))
    
    teacher_id = session['teacher_id']
    
    # Get statistics
    total_classes = Class.query.filter_by(teacher_id=teacher_id).count()
    total_students = db.session.query(Student).join(Class).filter(Class.teacher_id == teacher_id).count()
    
    # Get recent attendance records
    recent_attendance = db.session.query(Attendance).join(Student).join(Class).filter(
        Class.teacher_id == teacher_id
    ).order_by(Attendance.marked_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         total_classes=total_classes,
                         total_students=total_students,
                         recent_attendance=recent_attendance)

@main_bp.route('/classes')
def classes():
    if not require_login():
        return redirect(url_for('main.login'))
    
    teacher_id = session['teacher_id']
    teacher_classes = Class.query.filter_by(teacher_id=teacher_id).all()
    
    return render_template('classes.html', classes=teacher_classes)

@main_bp.route('/classes/add', methods=['POST'])
def add_class():
    if not require_login():
        return redirect(url_for('main.login'))
    
    name = request.form['name']
    subject = request.form['subject']
    teacher_id = session['teacher_id']
    
    new_class = Class(name=name, subject=subject, teacher_id=teacher_id)
    db.session.add(new_class)
    db.session.commit()
    
    flash('Class added successfully!', 'success')
    return redirect(url_for('main.classes'))

@main_bp.route('/classes/<int:class_id>/students')
def students(class_id):
    if not require_login():
        return redirect(url_for('main.login'))
    
    # Verify class belongs to logged-in teacher
    class_obj = Class.query.filter_by(id=class_id, teacher_id=session['teacher_id']).first()
    if not class_obj:
        flash('Class not found or access denied!', 'error')
        return redirect(url_for('main.classes'))
    
    students = Student.query.filter_by(class_id=class_id).all()
    
    return render_template('students.html', class_obj=class_obj, students=students)

@main_bp.route('/classes/<int:class_id>/students/add', methods=['POST'])
def add_student(class_id):
    if not require_login():
        return redirect(url_for('main.login'))
    
    # Verify class belongs to logged-in teacher
    class_obj = Class.query.filter_by(id=class_id, teacher_id=session['teacher_id']).first()
    if not class_obj:
        flash('Class not found or access denied!', 'error')
        return redirect(url_for('main.classes'))
    
    name = request.form['name']
    email = request.form['email']
    student_id = request.form['student_id']
    
    new_student = Student(name=name, email=email, student_id=student_id, class_id=class_id)
    db.session.add(new_student)
    db.session.commit()
    
    flash('Student added successfully!', 'success')
    return redirect(url_for('main.students', class_id=class_id))

@main_bp.route('/classes/<int:class_id>/students/bulk-import', methods=['POST'])
def bulk_import_students(class_id):
    if not require_login():
        return redirect(url_for('main.login'))
    
    # Check if bulk import is available
    if not BULK_IMPORT_AVAILABLE:
        flash('Bulk import feature is not available. Please install pandas to enable this feature.', 'error')
        return redirect(url_for('main.students', class_id=class_id))
    
    # Verify class belongs to logged-in teacher
    class_obj = Class.query.filter_by(id=class_id, teacher_id=session['teacher_id']).first()
    if not class_obj:
        flash('Class not found or access denied!', 'error')
        return redirect(url_for('main.classes'))
    
    # Check if file was uploaded
    if 'bulk_file' not in request.files:
        flash('No file was selected for upload!', 'error')
        return redirect(url_for('main.students', class_id=class_id))
    
    file = request.files['bulk_file']
    
    # Check if file is valid
    if file.filename == '':
        flash('No file was selected for upload!', 'error')
        return redirect(url_for('main.students', class_id=class_id))
    
    if not allowed_file(file.filename):
        flash('Invalid file format! Please upload .xlsx, .xls, or .csv files only.', 'error')
        return redirect(url_for('main.students', class_id=class_id))
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        # Get column mapping from form
        column_mapping = {
            'student_id': request.form.get('student_id_column', 'student_id'),
            'name': request.form.get('name_column', 'name'),
            'email': request.form.get('email_column', 'email')
        }
        
        # Get skip duplicates option
        skip_duplicates = 'skip_duplicates' in request.form
        
        # Process the import
        results = process_bulk_import(temp_path, class_id, column_mapping, skip_duplicates)
        
        # Generate user feedback
        if results['success']:
            success_msg = f"Successfully imported {results['imported']} students!"
            if results['skipped'] > 0:
                success_msg += f" ({results['skipped']} duplicates skipped)"
            flash(success_msg, 'success')
        else:
            flash('Import failed. Please check your file format and try again.', 'error')
        
        # Show any errors or warnings
        if results['errors']:
            for error in results['errors'][:10]:  # Limit to first 10 errors
                flash(error, 'warning')
            
            if len(results['errors']) > 10:
                flash(f"... and {len(results['errors']) - 10} more errors. Please check your file.", 'warning')
        
        logging.info(f"Bulk import completed for class {class_id}: {results['imported']} imported, {results['skipped']} skipped, {len(results['errors'])} errors")
        
    except Exception as e:
        logging.error(f"Bulk import failed for class {class_id}: {str(e)}")
        flash(f'Import failed: {str(e)}', 'error')
    
    return redirect(url_for('main.students', class_id=class_id))

@main_bp.route('/classes/<int:class_id>/attendance')
def attendance(class_id):
    if not require_login():
        return redirect(url_for('main.login'))
    
    # Verify class belongs to logged-in teacher
    class_obj = Class.query.filter_by(id=class_id, teacher_id=session['teacher_id']).first()
    if not class_obj:
        flash('Class not found or access denied!', 'error')
        return redirect(url_for('main.classes'))
    
    # Get attendance date from query parameter or use today
    attendance_date = request.args.get('date')
    if attendance_date:
        try:
            attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        except ValueError:
            attendance_date = date.today()
    else:
        attendance_date = date.today()
    
    students = Student.query.filter_by(class_id=class_id).all()
    
    # Get existing attendance records for the date
    existing_attendance = {}
    attendance_records = Attendance.query.filter_by(class_id=class_id, date=attendance_date).all()
    for record in attendance_records:
        existing_attendance[record.student_id] = record.status
    
    return render_template('attendance.html', 
                         class_obj=class_obj, 
                         students=students, 
                         attendance_date=attendance_date,
                         existing_attendance=existing_attendance)

@main_bp.route('/classes/<int:class_id>/attendance/mark', methods=['POST'])
def mark_attendance(class_id):
    if not require_login():
        return redirect(url_for('main.login'))
    
    # Verify class belongs to logged-in teacher
    class_obj = Class.query.filter_by(id=class_id, teacher_id=session['teacher_id']).first()
    if not class_obj:
        flash('Class not found or access denied!', 'error')
        return redirect(url_for('main.classes'))
    
    attendance_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    
    absent_students = []
    
    # Process attendance for each student
    students = Student.query.filter_by(class_id=class_id).all()
    for student in students:
        status = request.form.get(f'attendance_{student.id}', 'Absent')
        
        # Check if attendance already exists
        existing_attendance = Attendance.query.filter_by(
            student_id=student.id, 
            class_id=class_id, 
            date=attendance_date
        ).first()
        
        if existing_attendance:
            existing_attendance.status = status
            existing_attendance.marked_at = datetime.utcnow()
            # Reset email_sent flag if status changed to absent and email wasn't sent today
            if status == 'Absent' and not existing_attendance.email_sent:
                absent_students.append((student, existing_attendance))
        else:
            new_attendance = Attendance(
                student_id=student.id,
                class_id=class_id,
                date=attendance_date,
                status=status,
                email_sent=False
            )
            db.session.add(new_attendance)
            
            # Collect absent students for email notification
            if status == 'Absent':
                absent_students.append((student, new_attendance))
    
    db.session.commit()
    
    # Send email notifications to absent students (only once per day)
    emails_sent = 0
    if absent_students:
        teacher = Teacher.query.get(session['teacher_id'])
        for student, attendance_record in absent_students:
            # Only send email if not already sent for this date
            if not attendance_record.email_sent:
                try:
                    email_success = send_absence_notification(student, class_obj, attendance_date, teacher)
                    if email_success:
                        attendance_record.email_sent = True
                        emails_sent += 1
                        logging.info(f"Absence email sent to {student.email}")
                    else:
                        logging.warning(f"Failed to send email to {student.email} - SMTP not configured")
                except Exception as e:
                    logging.error(f"Failed to send email to {student.email}: {str(e)}")
    
    db.session.commit()
    
    flash(f'Attendance marked successfully for {len(students)} students!', 'success')
    if emails_sent > 0:
        flash(f'Email notifications sent to {emails_sent} absent students.', 'info')
    elif absent_students and emails_sent == 0:
        flash('Attendance marked but emails not sent. Please configure SMTP settings.', 'warning')
    
    return redirect(url_for('main.attendance', class_id=class_id, date=attendance_date.strftime('%Y-%m-%d')))

@main_bp.route('/history')
def history():
    if not require_login():
        return redirect(url_for('main.login'))
    
    teacher_id = session['teacher_id']
    
    # Get filter parameters
    class_id = request.args.get('class_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = db.session.query(Attendance).join(Student).join(Class).filter(Class.teacher_id == teacher_id)
    
    # Apply filters
    if class_id:
        query = query.filter(Attendance.class_id == class_id)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date >= start_date)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date <= end_date)
        except ValueError:
            pass
    
    # Get attendance records
    attendance_records = query.order_by(Attendance.date.desc(), Attendance.marked_at.desc()).all()
    
    # Get teacher's classes for filter dropdown
    teacher_classes = Class.query.filter_by(teacher_id=teacher_id).all()
    
    return render_template('history.html', 
                         attendance_records=attendance_records,
                         teacher_classes=teacher_classes,
                         current_class_id=class_id,
                         current_start_date=start_date,
                         current_end_date=end_date)

@main_bp.route('/export/excel')
def export_excel():
    if not require_login():
        return redirect(url_for('main.login'))
    
    teacher_id = session['teacher_id']
    class_id = request.args.get('class_id', type=int)
    
    if not class_id:
        flash('Please select a class to export.', 'error')
        return redirect(url_for('main.history'))
    
    # Verify class belongs to teacher
    class_obj = Class.query.filter_by(id=class_id, teacher_id=teacher_id).first()
    if not class_obj:
        flash('Class not found or access denied!', 'error')
        return redirect(url_for('main.history'))
    
    # Get date filters from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = None
    end_date = None
    
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format!', 'error')
        return redirect(url_for('main.history'))
    
    try:
        file_path = export_to_excel(class_obj, start_date, end_date)
        filename = f'{class_obj.name}_attendance'
        if start_date and end_date:
            filename += f'_{start_date}_{end_date}'
        filename += '.xlsx'
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        logging.error(f"Excel export failed: {str(e)}")
        flash('Export failed. Please try again.', 'error')
        return redirect(url_for('main.history'))

@main_bp.route('/export/csv')
def export_csv():
    if not require_login():
        return redirect(url_for('main.login'))
    
    teacher_id = session['teacher_id']
    class_id = request.args.get('class_id', type=int)
    
    if not class_id:
        flash('Please select a class to export.', 'error')
        return redirect(url_for('main.history'))
    
    # Verify class belongs to teacher
    class_obj = Class.query.filter_by(id=class_id, teacher_id=teacher_id).first()
    if not class_obj:
        flash('Class not found or access denied!', 'error')
        return redirect(url_for('main.history'))
    
    # Get date filters from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = None
    end_date = None
    
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format!', 'error')
        return redirect(url_for('main.history'))
    
    try:
        file_path = export_to_csv(class_obj, start_date, end_date)
        filename = f'{class_obj.name}_attendance'
        if start_date and end_date:
            filename += f'_{start_date}_{end_date}'
        filename += '.csv'
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        logging.error(f"CSV export failed: {str(e)}")
        flash('Export failed. Please try again.', 'error')
        return redirect(url_for('main.history'))

@main_bp.route('/test-email', methods=['GET', 'POST'])
def test_email():
    if not require_login():
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        test_email_address = request.form['test_email']
        teacher = Teacher.query.get(session.get('teacher_id'))
        if not teacher:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('main.login'))
        
        success, message = send_test_email(test_email_address, teacher)
        
        if success:
            flash(f'Test email sent successfully to {test_email_address}!', 'success')
        else:
            flash(f'Failed to send test email: {message}', 'error')
        
        return redirect(url_for('main.test_email'))
    
    return render_template('test_email.html')

@main_bp.route('/email-settings', methods=['GET', 'POST'])
def email_settings():
    if not require_login():
        return redirect(url_for('main.login'))
    
    teacher = Teacher.query.get(session.get('teacher_id'))
    if not teacher:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        # Update email settings
        teacher.smtp_email = request.form.get('smtp_email', '').strip()
        smtp_password = request.form.get('smtp_password', '').strip()
        
        if smtp_password:
            teacher.set_smtp_password(smtp_password)
        
        teacher.smtp_server = request.form.get('smtp_server', 'smtp.gmail.com').strip()
        teacher.smtp_port = int(request.form.get('smtp_port', 587))
        teacher.email_notifications_enabled = 'email_notifications_enabled' in request.form
        
        try:
            db.session.commit()
            flash('Email settings updated successfully!', 'success')
            
            # Test email connection if configured
            if teacher.has_email_config() and teacher.email_notifications_enabled:
                flash('Email configuration saved. You can now test it using the Test Email feature.', 'info')
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to update email settings: {str(e)}")
            flash('Failed to update email settings. Please try again.', 'error')
        
        return redirect(url_for('main.email_settings'))
    
    # GET request - show current settings
    config_status = {
        'username_configured': bool(teacher.smtp_email),
        'password_configured': bool(teacher.smtp_password),
        'server': teacher.smtp_server or 'smtp.gmail.com',
        'port': teacher.smtp_port or 587,
        'fully_configured': teacher.has_email_config(),
        'notifications_enabled': teacher.email_notifications_enabled
    }
    
    return render_template('email_settings.html', config_status=config_status, teacher=teacher)

@main_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if not require_login():
        return redirect(url_for('main.login'))
    
    teacher = Teacher.query.get(session.get('teacher_id'))
    if not teacher:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        # Update profile information
        teacher.name = request.form.get('name', '').strip()
        
        # Update password if provided
        new_password = request.form.get('new_password', '').strip()
        if new_password:
            confirm_password = request.form.get('confirm_password', '').strip()
            if new_password == confirm_password:
                teacher.set_password(new_password)
                flash('Password updated successfully!', 'success')
            else:
                flash('Passwords do not match!', 'error')
                return render_template('profile.html', teacher=teacher)
        
        try:
            db.session.commit()
            session['teacher_name'] = teacher.name  # Update session
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to update profile: {str(e)}")
            flash('Failed to update profile. Please try again.', 'error')
        
        return redirect(url_for('main.profile'))
    
    return render_template('profile.html', teacher=teacher)
