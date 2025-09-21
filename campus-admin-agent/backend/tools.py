# Tools: DB ops, analytics, notifications
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from db import get_db_session, Student, ActivityLog
from datetime import datetime, timedelta
import logging

# Set up logging for notifications
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Student Management Tools
def add_student(name: str, student_id: str, department: str, email: str) -> Dict[str, Any]:
    """Add a new student to the database"""
    try:
        db = get_db_session()
        # Check if student already exists
        existing_student = db.query(Student).filter(
            (Student.student_id == student_id) | (Student.email == email)
        ).first()
        
        if existing_student:
            db.close()
            return {"success": False, "message": "Student with this ID or email already exists"}
        
        new_student = Student(
            name=name,
            student_id=student_id,
            department=department,
            email=email
        )
        
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        
        # Log the activity
        activity = ActivityLog(
            student_id=student_id,
            activity_type="student_created",
            description=f"New student {name} added to {department}"
        )
        db.add(activity)
        db.commit()
        
        db.close()
        return {
            "success": True, 
            "message": f"Student {name} added successfully",
            "student": {
                "id": new_student.id,
                "student_id": new_student.student_id,
                "name": new_student.name,
                "department": new_student.department,
                "email": new_student.email
            }
        }
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error adding student: {str(e)}"}

def get_student(student_id: str) -> Dict[str, Any]:
    """Get student information by ID"""
    try:
        db = get_db_session()
        student = db.query(Student).filter(Student.student_id == student_id).first()
        
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
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error retrieving student: {str(e)}"}

def update_student(student_id: str, field: str, new_value: str) -> Dict[str, Any]:
    """Update a specific field of a student"""
    try:
        db = get_db_session()
        student = db.query(Student).filter(Student.student_id == student_id).first()
        
        if not student:
            db.close()
            return {"success": False, "message": "Student not found"}
        
        # Validate field
        valid_fields = ["name", "department", "email", "is_active"]
        if field not in valid_fields:
            db.close()
            return {"success": False, "message": f"Invalid field. Valid fields: {valid_fields}"}
        
        # Convert is_active to boolean if needed
        if field == "is_active":
            new_value = new_value.lower() in ["true", "1", "yes", "active"]
        
        setattr(student, field, new_value)
        student.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log the activity
        activity = ActivityLog(
            student_id=student_id,
            activity_type="profile_update",
            description=f"Updated {field} to {new_value}"
        )
        db.add(activity)
        db.commit()
        
        db.close()
        return {
            "success": True,
            "message": f"Student {student_id} updated successfully",
            "updated_field": field,
            "new_value": new_value
        }
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error updating student: {str(e)}"}

def delete_student(student_id: str) -> Dict[str, Any]:
    """Delete a student from the database"""
    try:
        db = get_db_session()
        student = db.query(Student).filter(Student.student_id == student_id).first()
        
        if not student:
            db.close()
            return {"success": False, "message": "Student not found"}
        
        student_name = student.name
        db.delete(student)
        
        # Log the activity
        activity = ActivityLog(
            student_id=student_id,
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
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error deleting student: {str(e)}"}

def list_students() -> Dict[str, Any]:
    """Get list of all students"""
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

# Campus Analytics Tools
def get_total_students() -> Dict[str, Any]:
    """Get total number of students"""
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

def get_students_by_department() -> Dict[str, Any]:
    """Get student count grouped by department"""
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

def get_recent_onboarded_students(limit: int = 5) -> Dict[str, Any]:
    """Get recently onboarded students"""
    try:
        db = get_db_session()
        recent_students = db.query(Student).order_by(
            desc(Student.created_at)
        ).limit(limit).all()
        
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
            "limit": limit
        }
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error getting recent students: {str(e)}"}

def get_active_students_last_7_days() -> Dict[str, Any]:
    """Get students who were active in the last 7 days (based on activity logs)"""
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

# Campus FAQ Tools
def get_cafeteria_timings() -> Dict[str, Any]:
    """Get cafeteria operating hours"""
    return {
        "success": True,
        "cafeteria_timings": {
            "breakfast": "7:00 AM - 10:00 AM",
            "lunch": "11:30 AM - 2:30 PM",
            "dinner": "6:00 PM - 9:00 PM",
            "weekend_hours": "10:00 AM - 8:00 PM"
        }
    }

def get_library_hours() -> Dict[str, Any]:
    """Get library operating hours"""
    return {
        "success": True,
        "library_hours": {
            "monday_friday": "8:00 AM - 10:00 PM",
            "saturday": "9:00 AM - 8:00 PM",
            "sunday": "10:00 AM - 6:00 PM",
            "study_rooms": "24/7 access with student ID"
        }
    }

def get_event_schedule() -> Dict[str, Any]:
    """Get upcoming campus events"""
    return {
        "success": True,
        "upcoming_events": [
            {
                "title": "Career Fair 2024",
                "date": "2024-03-15",
                "time": "10:00 AM - 4:00 PM",
                "location": "Main Auditorium"
            },
            {
                "title": "Tech Talk: AI in Education",
                "date": "2024-03-20",
                "time": "2:00 PM - 3:30 PM",
                "location": "Computer Science Building"
            },
            {
                "title": "Cultural Festival",
                "date": "2024-03-25",
                "time": "5:00 PM - 9:00 PM",
                "location": "Campus Grounds"
            }
        ]
    }

# Notification Tools
def send_email(student_id: str, message: str) -> Dict[str, Any]:
    """Send email to student (mock implementation)"""
    try:
        db = get_db_session()
        student = db.query(Student).filter(Student.student_id == student_id).first()
        
        if not student:
            db.close()
            return {"success": False, "message": "Student not found"}
        
        # Mock email sending
        logger.info(f"Email sent to {student.email}: {message}")
        
        # Log the activity
        activity = ActivityLog(
            student_id=student_id,
            activity_type="email_sent",
            description=f"Email sent: {message[:50]}..."
        )
        db.add(activity)
        db.commit()
        
        db.close()
        return {
            "success": True,
            "message": f"Email sent successfully to {student.name} ({student.email})",
            "recipient": student.email,
            "subject": message[:50] + "..." if len(message) > 50 else message
        }
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error sending email: {str(e)}"}

# Tool registry for the agent
TOOLS = {
    "add_student": add_student,
    "get_student": get_student,
    "update_student": update_student,
    "delete_student": delete_student,
    "list_students": list_students,
    "get_total_students": get_total_students,
    "get_students_by_department": get_students_by_department,
    "get_recent_onboarded_students": get_recent_onboarded_students,
    "get_active_students_last_7_days": get_active_students_last_7_days,
    "get_cafeteria_timings": get_cafeteria_timings,
    "get_library_hours": get_library_hours,
    "get_event_schedule": get_event_schedule,
    "send_email": send_email
}

