#!/usr/bin/env python3
"""
Comprehensive Test Script for Campus Admin Agent
This script tests all the fixes and validates the system works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports work correctly"""
    print("🧪 Testing Imports")
    print("=" * 50)
    
    try:
        # Test backend.tools imports
        from backend.tools import (
            add_student, get_student, update_student, delete_student, list_students,
            get_total_students, get_students_by_department, get_recent_onboarded_students,
            get_active_students_last_7_days, get_cafeteria_timings, get_library_hours,
            smit_info, StudentResponse, AddStudentRequest, GetStudentRequest,
            UpdateStudentRequest, DeleteStudentRequest, RecentStudentsRequest
        )
        print("✅ All backend.tools imports successful")
        
        # Test backend.agent imports
        from backend.agent import (
            student_management_agent, campus_analytics_agent, campus_info_agent,
            handoff_agent
        )
        print("✅ All backend.agent imports successful")
        
        # Test backend.db imports
        from backend.db import Student, ActivityLog, SessionLocal, get_db, engine, Base
        print("✅ All backend.db imports successful")
        
        # Test rag_test.py imports
        from rag_test import campus_info_agent as rag_agent
        print("✅ rag_test.py imports successful")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

def test_pydantic_models():
    """Test Pydantic validation models"""
    print("\n🔍 Testing Pydantic Models")
    print("=" * 50)
    
    try:
        from backend.tools import AddStudentRequest, GetStudentRequest, UpdateStudentRequest
        
        # Test valid AddStudentRequest
        valid_request = AddStudentRequest(
            name="John Doe",
            student_id="STU001",
            department="Computer Science",
            email="john.doe@university.edu"
        )
        print("✅ AddStudentRequest validation works")
        
        # Test valid GetStudentRequest
        valid_get = GetStudentRequest(student_id="STU001")
        print("✅ GetStudentRequest validation works")
        
        # Test valid UpdateStudentRequest
        valid_update = UpdateStudentRequest(
            student_id="STU001",
            field="name",
            new_value="Jane Doe"
        )
        print("✅ UpdateStudentRequest validation works")
        
    except Exception as e:
        print(f"❌ Pydantic model error: {e}")
        return False
    
    return True

def test_function_tools():
    """Test function tools work without database"""
    print("\n🛠️ Testing Function Tools")
    print("=" * 50)
    
    try:
        from backend.tools import get_cafeteria_timings, get_library_hours, smit_info
        
        # Test cafeteria timings
        result = get_cafeteria_timings()
        if result["success"]:
            print("✅ get_cafeteria_timings works")
        else:
            print(f"❌ get_cafeteria_timings failed: {result['message']}")
            return False
        
        # Test library hours
        result = get_library_hours()
        if result["success"]:
            print("✅ get_library_hours works")
        else:
            print(f"❌ get_library_hours failed: {result['message']}")
            return False
        
        # Test smit_info
        result = smit_info()
        if result["success"]:
            print("✅ smit_info works")
        else:
            print(f"❌ smit_info failed: {result['message']}")
            return False
        
    except Exception as e:
        print(f"❌ Function tool error: {e}")
        return False
    
    return True

def test_agent_initialization():
    """Test agent initialization"""
    print("\n🤖 Testing Agent Initialization")
    print("=" * 50)
    
    try:
        from backend.agent import (
            student_management_agent, campus_analytics_agent, 
            campus_info_agent, handoff_agent
        )
        
        # Check agent names
        agents = [
            ("Student Management", student_management_agent),
            ("Campus Analytics", campus_analytics_agent),
            ("Campus Info", campus_info_agent),
            ("Handoff Agent", handoff_agent)
        ]
        
        for name, agent in agents:
            if agent and hasattr(agent, 'name'):
                print(f"✅ {name} agent initialized: {agent.name}")
            else:
                print(f"❌ {name} agent not properly initialized")
                return False
        
    except Exception as e:
        print(f"❌ Agent initialization error: {e}")
        return False
    
    return True

def test_database_models():
    """Test database models"""
    print("\n🗄️ Testing Database Models")
    print("=" * 50)
    
    try:
        from backend.db import Student, ActivityLog, Base, engine
        
        # Check if models have required attributes
        student_attrs = ['id', 'student_id', 'name', 'department', 'email', 'is_active']
        for attr in student_attrs:
            if hasattr(Student, attr):
                print(f"✅ Student model has {attr}")
            else:
                print(f"❌ Student model missing {attr}")
                return False
        
        activity_attrs = ['id', 'student_id', 'activity_type', 'description', 'timestamp']
        for attr in activity_attrs:
            if hasattr(ActivityLog, attr):
                print(f"✅ ActivityLog model has {attr}")
            else:
                print(f"❌ ActivityLog model missing {attr}")
                return False
        
        print("✅ All database models properly defined")
        
    except Exception as e:
        print(f"❌ Database model error: {e}")
        return False
    
    return True

def test_error_handling():
    """Test error handling in function tools"""
    print("\n⚠️ Testing Error Handling")
    print("=" * 50)
    
    try:
        from backend.tools import add_student, get_student
        
        # Test validation error handling
        result = add_student(
            name="",  # Empty name should fail validation
            student_id="ab",  # Too short
            department="",  # Empty department
            email="invalid-email"  # Invalid email
        )
        
        if not result["success"] and "Validation error" in result["message"]:
            print("✅ Validation error handling works")
        else:
            print(f"❌ Validation error handling failed: {result}")
            return False
        
        # Test student not found error
        result = get_student("NONEXISTENT")
        if not result["success"] and "Student not found" in result["message"]:
            print("✅ Student not found error handling works")
        else:
            print(f"❌ Student not found error handling failed: {result}")
            return False
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🏫 Campus Admin Agent - Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Pydantic Models", test_pydantic_models),
        ("Function Tools", test_function_tools),
        ("Agent Initialization", test_agent_initialization),
        ("Database Models", test_database_models),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is working correctly.")
        print("\n💡 Next steps:")
        print("• Set up your .env file with GEMINI_API_KEY and DATABASE_URL")
        print("• Run 'python backend/db.py' to create database tables")
        print("• Run 'python backend/agent.py' to start the interactive agent")
        print("• Run 'python rag_test.py' to test the RAG functionality")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

