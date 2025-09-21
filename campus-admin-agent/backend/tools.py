from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool
from dotenv import load_dotenv
# from db import get_db, Student, ActivityLog, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr, validator
from db import get_db, Student, ActivityLog, SessionLocal
import os
import logging

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# PYDANTIC VALIDATION MODELS
# =============================================================================

class AddStudentRequest(BaseModel):
    """Validation model for adding a new student"""
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the student")
    student_id: str = Field(..., min_length=3, max_length=50, description="Unique student identifier")
    department: str = Field(..., min_length=2, max_length=100, description="Department the student belongs to")
    email: EmailStr = Field(..., description="Student's email address")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty or just whitespace')
        return v.strip().title()
    
    @validator('student_id')
    def validate_student_id(cls, v):
        if not v.strip():
            raise ValueError('Student ID cannot be empty or just whitespace')
        return v.strip().upper()
    
    @validator('department')
    def validate_department(cls, v):
        if not v.strip():
            raise ValueError('Department cannot be empty or just whitespace')
        return v.strip().title()

class GetStudentRequest(BaseModel):
    """Validation model for getting student information"""
    student_id: str = Field(..., min_length=3, max_length=50, description="Unique student identifier")
    
    @validator('student_id')
    def validate_student_id(cls, v):
        if not v.strip():
            raise ValueError('Student ID cannot be empty or just whitespace')
        return v.strip().upper()

class UpdateStudentRequest(BaseModel):
    """Validation model for updating student information"""
    student_id: str = Field(..., min_length=3, max_length=50, description="Unique student identifier")
    field: str = Field(..., description="Field to update")
    new_value: str = Field(..., description="New value for the field")
    
    @validator('student_id')
    def validate_student_id(cls, v):
        if not v.strip():
            raise ValueError('Student ID cannot be empty or just whitespace')
        return v.strip().upper()
    
    @validator('field')
    def validate_field(cls, v):
        valid_fields = ["name", "department", "email", "is_active"]
        if v not in valid_fields:
            raise ValueError(f'Invalid field. Valid fields: {valid_fields}')
        return v
    
    @validator('new_value')
    def validate_new_value(cls, v, values):
        if 'field' in values:
            field = values['field']
            if field == 'name' and len(v.strip()) < 2:
                raise ValueError('Name must be at least 2 characters long')
            elif field == 'department' and len(v.strip()) < 2:
                raise ValueError('Department must be at least 2 characters long')
            elif field == 'email' and '@' not in v:
                raise ValueError('Invalid email format')
        return v.strip() if isinstance(v, str) else v

class DeleteStudentRequest(BaseModel):
    """Validation model for deleting a student"""
    student_id: str = Field(..., min_length=3, max_length=50, description="Unique student identifier")
    
    @validator('student_id')
    def validate_student_id(cls, v):
        if not v.strip():
            raise ValueError('Student ID cannot be empty or just whitespace')
        return v.strip().upper()

class RecentStudentsRequest(BaseModel):
    """Validation model for getting recent students"""
    limit: int = Field(default=5, ge=1, le=50, description="Maximum number of recent students to return")

class StudentResponse(BaseModel):
    """Response model for student data"""
    id: int
    student_id: str
    name: str
    department: str
    email: str
    is_active: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ApiResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Helper function to get database session
def get_db_session():
    """Get database session from SessionLocal in db.py"""
    return SessionLocal()

# =============================================================================
# STUDENT MANAGEMENT TOOLS
# =============================================================================

@function_tool
def add_student(name: str, student_id: str, department: str, email: str) -> Dict[str, Any]:
    """Add a new student to the database
    
    Args:
        name: Full name of the student
        student_id: Unique student identifier
        department: Department the student belongs to
        email: Student's email address
        
    Returns:
        Dictionary with success status and student information
    """
    try:
        # Validate input using Pydantic model
        request = AddStudentRequest(
            name=name,
            student_id=student_id,
            department=department,
            email=email
        )
        
        db = get_db_session()
        # Check if student already exists
        existing_student = db.query(Student).filter(
            (Student.student_id == request.student_id) | (Student.email == request.email)
        ).first()
        
        if existing_student:
            db.close()
            return {"success": False, "message": "Student with this ID or email already exists"}
        
        new_student = Student(
            name=request.name,
            student_id=request.student_id,
            department=request.department,
            email=request.email
        )
        
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        
        # Log the activity
        activity = ActivityLog(
            student_id=request.student_id,
            activity_type="student_created",
            description=f"New student {request.name} added to {request.department}"
        )
        db.add(activity)
        db.commit()
        
        db.close()
        return {
            "success": True, 
            "message": f"Student {request.name} added successfully",
            "student": {
                "id": new_student.id,
                "student_id": new_student.student_id,
                "name": new_student.name,
                "department": new_student.department,
                "email": new_student.email
            }
        }
    except ValueError as e:
        return {"success": False, "message": f"Validation error: {str(e)}"}
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error adding student: {str(e)}"}

@function_tool
def get_student(student_id: str) -> Dict[str, Any]:
    """Get student information by ID
    
    Args:
        student_id: Unique student identifier
        
    Returns:
        Dictionary with success status and student information
    """
    try:
        # Validate input using Pydantic model
        request = GetStudentRequest(student_id=student_id)
        
        db = get_db_session()
        student = db.query(Student).filter(Student.student_id == request.student_id).first()
        
        if not student:
            db.close()
            return {"success": False, "message": "Student not found"}
        
        db.close()
        return {
            "success": True,
            "student": {
                "id": student.id,
                "student_id": student.student_id,
                "name": student.name,
                "department": student.department,
                "email": student.email,
                "is_active": student.is_active,
                "created_at": student.created_at.isoformat(),
                "updated_at": student.updated_at.isoformat()
            }
        }
    except ValueError as e:
        return {"success": False, "message": f"Validation error: {str(e)}"}
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error retrieving student: {str(e)}"}

@function_tool
def update_student(student_id: str, field: str, new_value: str) -> Dict[str, Any]:
    """Update a specific field of a student
    
    Args:
        student_id: Unique student identifier
        field: Field to update (name, department, email, is_active)
        new_value: New value for the field
        
    Returns:
        Dictionary with success status and update information
    """
    try:
        # Validate input using Pydantic model
        request = UpdateStudentRequest(
            student_id=student_id,
            field=field,
            new_value=new_value
        )
        
        db = get_db_session()
        student = db.query(Student).filter(Student.student_id == request.student_id).first()
        
        if not student:
            db.close()
            return {"success": False, "message": "Student not found"}
        
        # Convert is_active to boolean if needed
        if request.field == "is_active":
            request.new_value = request.new_value.lower() in ["true", "1", "yes", "active"]
        
        setattr(student, request.field, request.new_value)
        student.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log the activity
        activity = ActivityLog(
            student_id=request.student_id,
            activity_type="profile_update",
            description=f"Updated {request.field} to {request.new_value}"
        )
        db.add(activity)
        db.commit()
        
        db.close()
        return {
            "success": True,
            "message": f"Student {request.student_id} updated successfully",
            "updated_field": request.field,
            "new_value": request.new_value
        }
    except ValueError as e:
        return {"success": False, "message": f"Validation error: {str(e)}"}
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error updating student: {str(e)}"}

@function_tool
def delete_student(student_id: str) -> Dict[str, Any]:
    """Delete a student from the database
    
    Args:
        student_id: Unique student identifier
        
    Returns:
        Dictionary with success status and deletion information
    """
    try:
        # Validate input using Pydantic model
        request = DeleteStudentRequest(student_id=student_id)
        
        db = get_db_session()
        student = db.query(Student).filter(Student.student_id == request.student_id).first()
        
        if not student:
            db.close()
            return {"success": False, "message": "Student not found"}
        
        student_name = student.name
        db.delete(student)
        
        # Log the activity
        activity = ActivityLog(
            student_id=request.student_id,
            activity_type="student_deleted",
            description=f"Student {student_name} deleted"
        )
        db.add(activity)
        db.commit()
        
        db.close()
        return {
            "success": True,
            "message": f"Student {student_name} deleted successfully"
        }
    except ValueError as e:
        return {"success": False, "message": f"Validation error: {str(e)}"}
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error deleting student: {str(e)}"}

@function_tool
def list_students() -> Dict[str, Any]:
    """Get list of all students
    
    Returns:
        Dictionary with success status and list of all students
    """
    try:
        db = get_db_session()
        students = db.query(Student).all()
        
        student_list = []
        for student in students:
            student_list.append({
                "id": student.id,
                "student_id": student.student_id,
                "name": student.name,
                "department": student.department,
                "email": student.email,
                "is_active": student.is_active,
                "created_at": student.created_at.isoformat()
            })
        
        db.close()
        return {
            "success": True,
            "students": student_list,
            "total_count": len(student_list)
        }
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error retrieving students: {str(e)}"}

# =============================================================================
# CAMPUS ANALYTICS TOOLS
# =============================================================================

@function_tool
def get_total_students() -> Dict[str, Any]:
    """Get total number of students with active/inactive breakdown
    
    Returns:
        Dictionary with success status and student count statistics
    """
    try:
        db = get_db_session()
        total = db.query(Student).count()
        active = db.query(Student).filter(Student.is_active == True).count()
        inactive = total - active
        
        db.close()
        return {
            "success": True,
            "total_students": total,
            "active_students": active,
            "inactive_students": inactive
        }
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error getting student count: {str(e)}"}

@function_tool
def get_students_by_department() -> Dict[str, Any]:
    """Get student count grouped by department
    
    Returns:
        Dictionary with success status and department-wise student counts
    """
    try:
        db = get_db_session()
        dept_counts = db.query(
            Student.department,
            func.count(Student.id).label('count')
        ).group_by(Student.department).all()
        
        department_data = []
        for dept, count in dept_counts:
            department_data.append({
                "department": dept,
                "count": count
            })
        
        db.close()
        return {
            "success": True,
            "departments": department_data
        }
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error getting department data: {str(e)}"}

@function_tool
def get_recent_onboarded_students(limit: int = 5) -> Dict[str, Any]:
    """Get recently onboarded students
    
    Args:
        limit: Maximum number of recent students to return (default: 5)
        
    Returns:
        Dictionary with success status and list of recent students
    """
    try:
        # Validate input using Pydantic model
        request = RecentStudentsRequest(limit=limit)
        
        db = get_db_session()
        recent_students = db.query(Student).order_by(
            desc(Student.created_at)
        ).limit(request.limit).all()
        
        students = []
        for student in recent_students:
            students.append({
                "student_id": student.student_id,
                "name": student.name,
                "department": student.department,
                "email": student.email,
                "created_at": student.created_at.isoformat()
            })
        
        db.close()
        return {
            "success": True,
            "recent_students": students,
            "limit": request.limit
        }
    except ValueError as e:
        return {"success": False, "message": f"Validation error: {str(e)}"}
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error getting recent students: {str(e)}"}

@function_tool
def get_active_students_last_7_days() -> Dict[str, Any]:
    """Get students who were active in the last 7 days (based on activity logs)
    
    Returns:
        Dictionary with success status and list of active students
    """
    try:
        db = get_db_session()
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        active_students = db.query(ActivityLog.student_id).filter(
            ActivityLog.timestamp >= seven_days_ago
        ).distinct().all()
        
        student_ids = [student[0] for student in active_students]
        
        # Get student details
        students = db.query(Student).filter(
            Student.student_id.in_(student_ids)
        ).all()
        
        student_list = []
        for student in students:
            student_list.append({
                "student_id": student.student_id,
                "name": student.name,
                "department": student.department,
                "email": student.email
            })
        
        db.close()
        return {
            "success": True,
            "active_students": student_list,
            "count": len(student_list),
            "period": "last_7_days"
        }
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error getting active students: {str(e)}"}

# =============================================================================
# CAMPUS FAQ TOOLS
# =============================================================================

@function_tool
def get_cafeteria_timings() -> Dict[str, Any]:
    """Get cafeteria operating hours
    
    Returns:
        Dictionary with success status and cafeteria timing information
    """
    return {
        "success": True,
        "cafeteria_timings": {
            "campus_name": "Saylani Campus",
            "Campus Cafeteria": "8:00 AM - 8:00 PM",
            "breakfast": "7:00 AM - 10:00 AM",
            "lunch": "11:30 AM - 2:30 PM",
            "dinner": "6:00 PM - 9:00 PM",
            "weekend_hours": "10:00 AM - 8:00 PM"
        }
    }

@function_tool
def get_library_hours() -> Dict[str, Any]:
    """Get library operating hours
    
    Returns:
        Dictionary with success status and library hours information
    """
    return {
        "success": True,
        "library_hours": {
            "campus_name": "Saylani Campus",
            "library_name": "Saylani Library",
            "monday_friday": "8:00 AM - 10:00 PM",
            "saturday": "9:00 AM - 8:00 PM",
            "sunday": "10:00 AM - 6:00 PM",
            "study_rooms": "24/7 access with student ID"
        }
    }



# CAMPUS_INFO = """Saylani Mass IT Training (S.M.I.T.)
# Institution: Saylani Welfare International Trust
# Program: S.M.I.T. (Saylani Mass IT Training)
# Description: Empowering youth with cutting-edge IT skills for a brighter future.
# Courses Offered:
#   - Web Development (HTML, CSS, JavaScript, React)
#   - Mobile App Development (Flutter, React Native)
#   - Graphic Designing (Adobe Photoshop, Illustrator)
#   - Python Programming
#   - Data Science & Machine Learning
#   - Cloud Computing (AWS, Azure)
# Location: Multiple campuses (Karachi, Lahore, Islamabad, Faisalabad)
# Timings: 24/7 flexible batches (Morning, Afternoon, Evening, Weekend)
# Duration: 3-6 months per course
# Eligibility: Open to all (Beginners to Advanced)
# Fee Structure: Free of cost
# Contact: info@saylaniwelfare.com | +92-123-456-7890
# Address: Saylani Welfare Head Office, A-25, Bahadurabad, Karachi
# Registration: Online at www.saylaniwelfare.com/smit
# Start Date: Rolling admissions, new batches every month
# Additional Services: Career counseling, job placement support, freelancing guidance
# Motto: "Skill Up, Rise Up!"""

# @function_tool
# def smit_info() -> Dict[str, Any]:
#     """Get information about Saylani Mass IT Training (S.M.I.T.)
#     Returns:
#         Dictionary with success status and S.M.I.T. information
#     """
#     return {
#         "success": True,
#         "smit_info": CAMPUS_INFO
#     }
# =============================================================================
# TOOL REGISTRY FOR AGENT
# =============================================================================

# All function tools are automatically registered when decorated with @function_tool
# The agent will automatically discover and use these tools