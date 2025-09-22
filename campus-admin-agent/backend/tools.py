import asyncio
from dotenv import load_dotenv
from sqlalchemy import func, desc, or_
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr, validator
from backend.db import get_db, Student, ActivityLog, SessionLocal
from dotenv import load_dotenv
import os
import logging
import re
import uuid
from agents import function_tool

load_dotenv()

def student_to_response(student):
    return {
        "id": student.id,
        "student_id": student.student_id,
        "name": student.name,
        "department": student.department,
        "email": student.email,
        "is_active": student.is_active,
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "updated_at": student.updated_at.isoformat() if student.updated_at else None,
    }

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('student_management_tools.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# PKT timezone (UTC+5)
PKT_OFFSET = timedelta(hours=5)
def get_pkt_time():
    """Get current time in PKT (UTC+5)"""
    return datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(PKT_OFFSET))

# Fix database session management - remove async context manager that conflicts with sync operations
# Input sanitization helper
def sanitize_input(value: str) -> str:
    """Sanitize input strings to prevent injection attacks"""
    if not isinstance(value, str):
        return value
    value = re.sub(r'[<>;{}]', '', value)
    return ' '.join(value.strip().split())

# =============================================================================
# PYDANTIC VALIDATION MODELS
# =============================================================================

class AddStudentRequest(BaseModel):
    """Validation model for adding a new student"""
    name: str = Field(..., min_length=2, max_length=100, description="Student's full name")
    student_id: str = Field(..., min_length=3, max_length=50, description="Unique student identifier")
    department: str = Field(..., min_length=2, max_length=100, description="Academic department")
    email: EmailStr = Field(..., description="Student's email address")
    
    @validator('name')
    def validate_name(cls, v):
        v = sanitize_input(v)
        if not v:
            raise ValueError('Name cannot be empty')
        return v.title()
    
    @validator('student_id')
    def validate_student_id(cls, v):
        v = sanitize_input(v)
        if not v or not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('Invalid student ID format')
        return v.upper()
    
    @validator('department')
    def validate_department(cls, v):
        v = sanitize_input(v)
        if not v:
            raise ValueError('Department cannot be empty')
        return v.title()

class GetStudentRequest(BaseModel):
    """Validation model for retrieving student information"""
    student_id: str = Field(..., min_length=3, max_length=50, description="Unique student identifier")
    
    @validator('student_id')
    def validate_student_id(cls, v):
        v = sanitize_input(v)
        if not v:
            raise ValueError('Student ID cannot be empty')
        return v.upper()

class UpdateStudentRequest(BaseModel):
    """Validation model for updating student information"""
    student_id: str = Field(..., min_length=3, max_length=50, description="Unique student identifier")
    field: str = Field(..., description="Field to update (name, department, email, is_active)")
    new_value: str = Field(..., description="New value for the field")
    
    @validator('student_id')
    def validate_student_id(cls, v):
        v = sanitize_input(v)
        if not v:
            raise ValueError('Student ID cannot be empty')
        return v.upper()
    
    @validator('field')
    def validate_field(cls, v):
        valid_fields = ["name", "department", "email", "is_active"]
        if v not in valid_fields:
            raise ValueError(f'Invalid field. Valid fields: {valid_fields}')
        return v
    
    @validator('new_value')
    def validate_new_value(cls, v, values):
        v = sanitize_input(v)
        if 'field' in values:
            field = values['field']
            if field == 'name' and len(v) < 2:
                raise ValueError('Name must be at least 2 characters')
            elif field == 'department' and len(v) < 2:
                raise ValueError('Department must be at least 2 characters')
            elif field == 'email' and '@' not in v:
                raise ValueError('Invalid email format')
        return v

class DeleteStudentRequest(BaseModel):
    """Validation model for deleting a student"""
    student_id: str = Field(..., min_length=3, max_length=50, description="Unique student identifier")
    
    @validator('student_id')
    def validate_student_id(cls, v):
        v = sanitize_input(v)
        if not v:
            raise ValueError('Student ID cannot be empty')
        return v.upper()

class RecentStudentsRequest(BaseModel):
    """Validation model for getting recent students"""
    limit: int = Field(default=5, ge=1, le=100, description="Maximum number of students to return")

class StudentResponse(BaseModel):
    """Response model for student data"""
    id: int = Field(..., description="Database ID")
    student_id: str = Field(..., description="Unique student identifier")
    name: str = Field(..., description="Student's full name")
    department: str = Field(..., description="Academic department")
    email: str = Field(..., description="Student's email")
    is_active: Optional[bool] = Field(None, description="Active status")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

class ApiResponse(BaseModel):
    """Standard API response format for agent consumption"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier")

# =============================================================================
# STUDENT MANAGEMENT TOOLS
# =============================================================================

@function_tool
def add_student(name: str, student_id: str, department: str, email: str) -> Dict[str, Any]:
    """Add a new student to the database
    
    Args:
        name: Full name of the student
        student_id: Unique student identifier
        department: Academic department
        email: Student's email address
    """
    request_id = str(uuid.uuid4())
    try:
        request = AddStudentRequest(name=name, student_id=student_id, department=department, email=email)
        logger.info(f"Agent request {request_id}: Adding student {request.student_id}")
        
        with SessionLocal() as db:
            existing_student = db.query(Student).filter(
                or_(Student.student_id == request.student_id, Student.email == request.email)
            ).first()
            
            if existing_student:
                return ApiResponse(
                    success=False,
                    message="Student with this ID or email already exists",
                    request_id=request_id
                ).dict()
            
            new_student = Student(
                name=request.name,
                student_id=request.student_id,
                department=request.department,
                email=request.email,
                created_at=get_pkt_time(),
                updated_at=get_pkt_time()
            )
            
            db.add(new_student)
            db.flush()
            
            activity = ActivityLog(
                student_id=request.student_id,
                activity_type="student_created",
                description=f"New student {request.name} added to {request.department}",
                timestamp=get_pkt_time()
            )
            db.add(activity)
            db.commit()
            
            return ApiResponse(
                success=True,
                message=f"Student {request.name} added successfully",
                    data={"student": student_to_response(new_student)},
                request_id=request_id
            ).dict()
    except ValueError as e:
        logger.error(f"Agent request {request_id}: Validation error adding student: {str(e)}")
        return ApiResponse(success=False, message=f"Validation error: {str(e)}", request_id=request_id).dict()
    except Exception as e:
        logger.error(f"Agent request {request_id}: Error adding student: {str(e)}")
        return ApiResponse(success=False, message=f"Error adding student: {str(e)}", request_id=request_id).dict()

@function_tool
async def get_student(student_id: str) -> Dict[str, Any]:
    """Get student information by ID
    
    Args:
        student_id: Unique student identifier
    """
    request_id = str(uuid.uuid4())
    try:
        request = GetStudentRequest(student_id=student_id)
        logger.info(f"Agent request {request_id}: Retrieving student {request.student_id}")
        
        with SessionLocal() as db:
            student = db.query(Student).filter(Student.student_id == request.student_id).first()
            
            if not student:
                return ApiResponse(success=False, message="Student not found", request_id=request_id).dict()
            
            return ApiResponse(
                success=True,
                message="Student retrieved successfully",
                    data={"student": student_to_response(student)},
                request_id=request_id
            ).dict()
    except ValueError as e:
        logger.error(f"Agent request {request_id}: Validation error getting student: {str(e)}")
        return ApiResponse(success=False, message=f"Validation error: {str(e)}", request_id=request_id).dict()
    except Exception as e:
        logger.error(f"Agent request {request_id}: Error getting student: {str(e)}")
        return ApiResponse(success=False, message=f"Error retrieving student: {str(e)}", request_id=request_id).dict()

@function_tool
async def update_student(student_id: str, field: str, new_value: str) -> Dict[str, Any]:
    """Update a specific field of a student
    
    Args:
        student_id: Unique student identifier
        field: Field to update (name, department, email, is_active)
        new_value: New value for the field
    """
    request_id = str(uuid.uuid4())
    try:
        request = UpdateStudentRequest(student_id=student_id, field=field, new_value=new_value)
        logger.info(f"Agent request {request_id}: Updating student {request.student_id}")
        
        with SessionLocal() as db:
            student = db.query(Student).filter(Student.student_id == request.student_id).first()
            
            if not student:
                return ApiResponse(success=False, message="Student not found", request_id=request_id).dict()
            
            if request.field == "is_active":
                request.new_value = request.new_value.lower() in ["true", "1", "yes", "active"]
            
            setattr(student, request.field, request.new_value)
            student.updated_at = get_pkt_time()
            
            activity = ActivityLog(
                student_id=request.student_id,
                activity_type="profile_update",
                description=f"Updated {request.field} to {request.new_value}",
                timestamp=get_pkt_time()
            )
            db.add(activity)
            db.commit()
            
            return ApiResponse(
                success=True,
                message=f"Student {request.student_id} updated successfully",
                data={"updated_field": request.field, "new_value": request.new_value},
                request_id=request_id
            ).dict()
    except ValueError as e:
        logger.error(f"Agent request {request_id}: Validation error updating student: {str(e)}")
        return ApiResponse(success=False, message=f"Validation error: {str(e)}", request_id=request_id).dict()
    except Exception as e:
        logger.error(f"Agent request {request_id}: Error updating student: {str(e)}")
        return ApiResponse(success=False, message=f"Error updating student: {str(e)}", request_id=request_id).dict()

@function_tool
async def delete_student(student_id: str) -> Dict[str, Any]:
    """Delete a student from the database
    
    Args:
        student_id: Unique student identifier
    """
    request_id = str(uuid.uuid4())
    try:
        request = DeleteStudentRequest(student_id=student_id)
        logger.info(f"Agent request {request_id}: Deleting student {request.student_id}")
        
        with SessionLocal() as db:
            student = db.query(Student).filter(Student.student_id == request.student_id).first()
            
            if not student:
                return ApiResponse(success=False, message="Student not found", request_id=request_id).dict()
            
            student_name = student.name
            db.delete(student)
            
            activity = ActivityLog(
                student_id=request.student_id,
                activity_type="student_deleted",
                description=f"Student {student_name} deleted",
                timestamp=get_pkt_time()
            )
            db.add(activity)
            db.commit()
            
            return ApiResponse(
                success=True,
                message=f"Student {student_name} deleted successfully",
                request_id=request_id
            ).dict()
    except ValueError as e:
        logger.error(f"Agent request {request_id}: Validation error deleting student: {str(e)}")
        return ApiResponse(success=False, message=f"Validation error: {str(e)}", request_id=request_id).dict()
    except Exception as e:
        logger.error(f"Agent request {request_id}: Error deleting student: {str(e)}")
        return ApiResponse(success=False, message=f"Error deleting student: {str(e)}", request_id=request_id).dict()

@function_tool
async def list_students() -> Dict[str, Any]:
    """Get list of all students"""
    request_id = str(uuid.uuid4())
    try:
        logger.info(f"Agent request {request_id}: Listing all students")
        with SessionLocal() as db:
            students = db.query(Student).all()
            student_list = [student_to_response(s) for s in students]
            return ApiResponse(
                success=True,
                message="List of all students retrieved successfully",
                data={"students": student_list, "total_count": len(student_list)},
                request_id=request_id
            ).dict()
    except Exception as e:
        logger.error(f"Agent request {request_id}: Error listing students: {str(e)}")
        return ApiResponse(success=False, message=f"Error retrieving students: {str(e)}", request_id=request_id).dict()

# =============================================================================
# CAMPUS ANALYTICS TOOLS
# =============================================================================

@function_tool
async def get_total_students() -> Dict[str, Any]:
    """Get total number of students with active/inactive breakdown"""
    request_id = str(uuid.uuid4())
    try:
        logger.info(f"Agent request {request_id}: Getting total student count")
        with SessionLocal() as db:
            total = db.query(Student).count()
            active = db.query(Student).filter(Student.is_active == True).count()
            
            return ApiResponse(
                success=True,
                message="Student count retrieved successfully",
                data={
                    "total_students": total,
                    "active_students": active,
                    "inactive_students": total - active
                },
                request_id=request_id
            ).dict()
    except Exception as e:
        logger.error(f"Agent request {request_id}: Error getting student count: {str(e)}")
        return ApiResponse(success=False, message=f"Error getting student count: {str(e)}", request_id=request_id).dict()

@function_tool
async def get_students_by_department() -> Dict[str, Any]:
    """Get student count grouped by department"""
    request_id = str(uuid.uuid4())
    try:
        logger.info(f"Agent request {request_id}: Getting student count by department")
        with SessionLocal() as db:
            dept_counts = db.query(
                Student.department,
                func.count(Student.id).label('count')
            ).group_by(Student.department).all()
            
            department_data = [{"department": dept, "count": count} for dept, count in dept_counts]
            
            return ApiResponse(
                success=True,
                message="Department counts retrieved successfully",
                data={"departments": department_data},
                request_id=request_id
            ).dict()
    except Exception as e:
        logger.error(f"Agent request {request_id}: Error getting department data: {str(e)}")
        return ApiResponse(success=False, message=f"Error getting department data: {str(e)}", request_id=request_id).dict()

@function_tool
async def get_recent_onboarded_students(limit: int = 5) -> Dict[str, Any]:
    """Get recently onboarded students
    
    Args:
        limit: Maximum number of recent students to return (default: 5)
    """
    request_id = str(uuid.uuid4())
    try:
        request = RecentStudentsRequest(limit=limit)
        logger.info(f"Agent request {request_id}: Getting recent students (limit: {request.limit})")
        
        with SessionLocal() as db:
            recent_students = db.query(Student).order_by(
                desc(Student.created_at)
            ).limit(request.limit).all()
            students = [student_to_response(s) for s in recent_students]
            return ApiResponse(
                success=True,
                message="Recent students retrieved successfully",
                data={"recent_students": students, "limit": request.limit},
                request_id=request_id
            ).dict()
    except ValueError as e:
        logger.error(f"Agent request {request_id}: Validation error getting recent students: {str(e)}")
        return ApiResponse(success=False, message=f"Validation error: {str(e)}", request_id=request_id).dict()
    except Exception as e:
        logger.error(f"Agent request {request_id}: Error getting recent students: {str(e)}")
        return ApiResponse(success=False, message=f"Error getting recent students: {str(e)}", request_id=request_id).dict()

@function_tool
async def get_active_students_last_7_days() -> Dict[str, Any]:
    """Get students who were active in the last 7 days (based on activity logs)"""
    request_id = str(uuid.uuid4())
    try:
        logger.info(f"Agent request {request_id}: Getting active students for last 7 days")
        with SessionLocal() as db:
            seven_days_ago = get_pkt_time() - timedelta(days=7)
            
            active_students = db.query(ActivityLog.student_id).filter(
                ActivityLog.timestamp >= seven_days_ago
            ).distinct().all()
            
            student_ids = [student[0] for student in active_students]
            
            students = db.query(Student).filter(
                Student.student_id.in_(student_ids)
            ).all()
            
            student_list = [student_to_response(s) for s in students]
            return ApiResponse(
                success=True,
                message="Active students retrieved successfully",
                data={
                    "active_students": student_list,
                    "count": len(student_list),
                    "period": "last_7_days"
                },
                request_id=request_id
            ).dict()
    except Exception as e:
        logger.error(f"Agent request {request_id}: Error getting active students: {str(e)}")
        return ApiResponse(success=False, message=f"Error getting active students: {str(e)}", request_id=request_id).dict()

# =============================================================================
# CAMPUS FAQ TOOLS
# =============================================================================

@function_tool
async def get_library_name() -> Dict[str, Any]:
    """Get the name of the campus library"""
    request_id = str(uuid.uuid4())
    logger.info(f"Agent request {request_id}: Getting library name")
    return ApiResponse(
        success=True,
        message="Library name retrieved successfully",
        data={"library_name": "Saylani Library"},
        request_id=request_id
    ).dict()

@function_tool
async def get_cafeteria_name() -> Dict[str, Any]:
    """Get the name of the campus cafeteria"""
    request_id = str(uuid.uuid4())
    logger.info(f"Agent request {request_id}: Getting cafeteria name")
    return ApiResponse(
        success=True,
        message="Cafeteria name retrieved successfully",
        data={"cafeteria_name": "Campus Cafeteria"},
        request_id=request_id
    ).dict()

@function_tool
async def get_cafeteria_timings() -> Dict[str, Any]:
    """Get cafeteria operating hours"""
    request_id = str(uuid.uuid4())
    logger.info(f"Agent request {request_id}: Getting cafeteria timings")
    return ApiResponse(
        success=True,
        message="Cafeteria timings retrieved successfully. The cafeteria name is 'Campus Cafeteria'.",
        data={
            "cafeteria_timings": {
                "campus_name": "Saylani Campus",
                "cafeteria_name": "Campus Cafeteria",
                "hours": "8:00 AM - 8:00 PM",
                "breakfast": "7:00 AM - 10:00 AM",
                "lunch": "11:30 AM - 2:30 PM",
                "dinner": "6:00 PM - 9:00 PM",
                "weekend_hours": "10:00 AM - 8:00 PM"
            }
        },
        request_id=request_id
    ).dict()

@function_tool
async def get_library_hours() -> Dict[str, Any]:
    """Get library operating hours"""
    request_id = str(uuid.uuid4())
    logger.info(f"Agent request {request_id}: Getting library hours")
    return ApiResponse(
        success=True,
        message="Library hours retrieved successfully. The library name is 'Saylani Library'.",
        data={
            "library_hours": {
                "campus_name": "Saylani Campus",
                "library_name": "Saylani Library",
                "monday_friday": "8:00 AM - 10:00 PM",
                "saturday": "9:00 AM - 8:00 PM",
                "sunday": "10:00 AM - 6:00 PM",
                "study_rooms": "24/7 access with student ID"
            }
        },
        request_id=request_id
    ).dict()

@function_tool
async def get_lunch_timing() -> Dict[str, Any]:
    """Get lunch timing information specifically"""
    request_id = str(uuid.uuid4())
    logger.info(f"Agent request {request_id}: Getting lunch timing")
    return ApiResponse(
        success=True,
        message="Lunch timing retrieved successfully",
        data={
            "lunch_timing": {
                "campus_name": "Saylani Campus",
                "lunch_hours": "11:30 AM - 2:30 PM",
                "service_type": "Lunch Service",
                "days": "Monday - Friday",
                "weekend_lunch": "Available during weekend cafeteria hours"
            }
        },
        request_id=request_id
    ).dict()

