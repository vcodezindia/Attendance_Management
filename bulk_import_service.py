"""
Bulk import service for reading Excel and CSV files to import students
"""
import pandas as pd
import os
import logging
from typing import List, Dict, Tuple
from werkzeug.utils import secure_filename
from models import Student
from database import db
from email_validator import validate_email, EmailNotValidError

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_file_data(file_path: str) -> pd.DataFrame:
    """Read data from Excel or CSV file"""
    try:
        if file_path.endswith('.csv'):
            # Try different encodings for CSV files
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not read CSV file with any supported encoding")
        else:
            # Read Excel file
            df = pd.read_excel(file_path, engine='openpyxl')
        
        return df
    
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        raise ValueError(f"Could not read file: {str(e)}")

def normalize_column_name(column_name: str) -> str:
    """Normalize column names for case-insensitive matching"""
    return str(column_name).lower().strip().replace(' ', '_')

def find_column(df: pd.DataFrame, possible_names: List[str]) -> str:
    """Find column by trying multiple possible names"""
    df_columns = {normalize_column_name(col): col for col in df.columns}
    
    for name in possible_names:
        normalized_name = normalize_column_name(name)
        if normalized_name in df_columns:
            return df_columns[normalized_name]
    
    return None

def validate_student_data(student_data: Dict) -> Tuple[bool, str]:
    """Validate individual student data"""
    # Check required fields
    if not student_data.get('student_id'):
        return False, "Student ID is required"
    
    if not student_data.get('name'):
        return False, "Name is required"
    
    if not student_data.get('email'):
        return False, "Email is required"
    
    # Validate email format
    try:
        validate_email(student_data['email'])
    except EmailNotValidError:
        return False, f"Invalid email format: {student_data['email']}"
    
    # Check for reasonable length limits
    if len(student_data['student_id']) > 50:
        return False, "Student ID too long (max 50 characters)"
    
    if len(student_data['name']) > 100:
        return False, "Name too long (max 100 characters)"
    
    if len(student_data['email']) > 120:
        return False, "Email too long (max 120 characters)"
    
    return True, ""

def process_bulk_import(file_path: str, class_id: int, column_mapping: Dict[str, str], 
                       skip_duplicates: bool = True) -> Dict:
    """
    Process bulk import of students from Excel/CSV file
    
    Args:
        file_path: Path to the uploaded file
        class_id: ID of the class to add students to
        column_mapping: Dictionary mapping data types to column names
        skip_duplicates: Whether to skip duplicate student IDs
    
    Returns:
        Dictionary with import results
    """
    results = {
        'success': False,
        'total_rows': 0,
        'imported': 0,
        'skipped': 0,
        'errors': [],
        'imported_students': []
    }
    
    try:
        # Read the file
        df = read_file_data(file_path)
        results['total_rows'] = len(df)
        
        if df.empty:
            results['errors'].append("File is empty or has no data rows")
            return results
        
        # Find columns based on mapping
        student_id_col = find_column(df, [
            column_mapping.get('student_id', 'student_id'),
            'student_id', 'id', 'student_number', 'roll_number'
        ])
        
        name_col = find_column(df, [
            column_mapping.get('name', 'name'),
            'name', 'full_name', 'student_name'
        ])
        
        email_col = find_column(df, [
            column_mapping.get('email', 'email'),
            'email', 'email_address', 'student_email'
        ])
        
        # Check if required columns were found
        missing_columns = []
        if not student_id_col:
            missing_columns.append("Student ID")
        if not name_col:
            missing_columns.append("Name")
        if not email_col:
            missing_columns.append("Email")
        
        if missing_columns:
            results['errors'].append(f"Could not find columns: {', '.join(missing_columns)}")
            return results
        
        # Get existing student IDs in this class to check for duplicates
        existing_student_ids = set()
        if skip_duplicates:
            existing_students = Student.query.filter_by(class_id=class_id).all()
            existing_student_ids = {s.student_id.lower() for s in existing_students}
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Extract data from row
                student_data = {
                    'student_id': str(row[student_id_col]).strip() if pd.notna(row[student_id_col]) else "",
                    'name': str(row[name_col]).strip() if pd.notna(row[name_col]) else "",
                    'email': str(row[email_col]).strip() if pd.notna(row[email_col]) else ""
                }
                
                # Skip empty rows
                if not any(student_data.values()):
                    continue
                
                # Validate student data
                is_valid, error_msg = validate_student_data(student_data)
                if not is_valid:
                    results['errors'].append(f"Row {index + 2}: {error_msg}")
                    continue
                
                # Check for duplicates
                if skip_duplicates and student_data['student_id'].lower() in existing_student_ids:
                    results['skipped'] += 1
                    results['errors'].append(f"Row {index + 2}: Student ID '{student_data['student_id']}' already exists (skipped)")
                    continue
                
                # Check if student with same ID already exists in database
                existing_student = Student.query.filter_by(
                    class_id=class_id, 
                    student_id=student_data['student_id']
                ).first()
                
                if existing_student:
                    if skip_duplicates:
                        results['skipped'] += 1
                        results['errors'].append(f"Row {index + 2}: Student ID '{student_data['student_id']}' already exists (skipped)")
                        continue
                    else:
                        results['errors'].append(f"Row {index + 2}: Student ID '{student_data['student_id']}' already exists")
                        continue
                
                # Create new student
                new_student = Student(
                    student_id=student_data['student_id'],
                    name=student_data['name'],
                    email=student_data['email'],
                    class_id=class_id
                )
                
                db.session.add(new_student)
                results['imported'] += 1
                results['imported_students'].append(student_data)
                
                # Add to existing IDs set to prevent duplicates within the same import
                existing_student_ids.add(student_data['student_id'].lower())
                
            except Exception as e:
                results['errors'].append(f"Row {index + 2}: {str(e)}")
                continue
        
        # Commit all changes
        if results['imported'] > 0:
            db.session.commit()
            results['success'] = True
            logging.info(f"Successfully imported {results['imported']} students to class {class_id}")
        else:
            db.session.rollback()
            if not results['errors']:
                results['errors'].append("No valid student data found to import")
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Bulk import failed: {str(e)}")
        results['errors'].append(f"Import failed: {str(e)}")
    
    finally:
        # Clean up the uploaded file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logging.warning(f"Could not delete uploaded file {file_path}: {str(e)}")
    
    return results