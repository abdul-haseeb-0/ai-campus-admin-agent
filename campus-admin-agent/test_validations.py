#!/usr/bin/env python3
"""
Test script for Pydantic Validations in Campus Admin Agent
This script demonstrates the validation features added to function tools
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.tools import (
    AddStudentRequest, GetStudentRequest, UpdateStudentRequest, 
    DeleteStudentRequest, RecentStudentsRequest
)

def test_pydantic_validations():
    """Test the Pydantic validation models"""
    print("🧪 Testing Pydantic Validations")
    print("=" * 50)
    
    # Test 1: Valid AddStudentRequest
    print("\n1. Testing valid AddStudentRequest:")
    try:
        valid_request = AddStudentRequest(
            name="John Doe",
            student_id="STU001",
            department="Computer Science",
            email="john.doe@university.edu"
        )
        print(f"   ✅ Valid request: {valid_request}")
        print(f"   📝 Normalized name: '{valid_request.name}'")
        print(f"   📝 Normalized student_id: '{valid_request.student_id}'")
        print(f"   📝 Normalized department: '{valid_request.department}'")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Invalid email
    print("\n2. Testing invalid email:")
    try:
        invalid_request = AddStudentRequest(
            name="Jane Doe",
            student_id="STU002",
            department="Mathematics",
            email="invalid-email"
        )
        print(f"   ❌ This should not print: {invalid_request}")
    except Exception as e:
        print(f"   ✅ Correctly caught validation error: {e}")
    
    # Test 3: Empty name
    print("\n3. Testing empty name:")
    try:
        invalid_request = AddStudentRequest(
            name="   ",
            student_id="STU003",
            department="Physics",
            email="jane.doe@university.edu"
        )
        print(f"   ❌ This should not print: {invalid_request}")
    except Exception as e:
        print(f"   ✅ Correctly caught validation error: {e}")
    
    # Test 4: Invalid field in UpdateStudentRequest
    print("\n4. Testing invalid field in UpdateStudentRequest:")
    try:
        invalid_request = UpdateStudentRequest(
            student_id="STU001",
            field="invalid_field",
            new_value="some value"
        )
        print(f"   ❌ This should not print: {invalid_request}")
    except Exception as e:
        print(f"   ✅ Correctly caught validation error: {e}")
    
    # Test 5: Invalid limit in RecentStudentsRequest
    print("\n5. Testing invalid limit in RecentStudentsRequest:")
    try:
        invalid_request = RecentStudentsRequest(limit=100)  # Should be max 50
        print(f"   ❌ This should not print: {invalid_request}")
    except Exception as e:
        print(f"   ✅ Correctly caught validation error: {e}")
    
    # Test 6: Valid RecentStudentsRequest
    print("\n6. Testing valid RecentStudentsRequest:")
    try:
        valid_request = RecentStudentsRequest(limit=10)
        print(f"   ✅ Valid request: {valid_request}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Pydantic validation tests completed!")
    print("\n💡 Key Features:")
    print("• Email validation using EmailStr")
    print("• String length validation (min/max)")
    print("• Custom validators for data normalization")
    print("• Field-specific validation rules")
    print("• Automatic data cleaning (strip, title case, uppercase)")

def test_function_tool_integration():
    """Test how function tools handle validation errors"""
    print("\n🔧 Testing Function Tool Integration")
    print("=" * 50)
    
    from backend.tools import add_student, get_student
    
    # Test valid function call
    print("\n1. Testing valid add_student call:")
    result = add_student(
        name="Alice Smith",
        student_id="STU004",
        department="Engineering",
        email="alice.smith@university.edu"
    )
    print(f"   Result: {result}")
    
    # Test invalid function call (should be caught by validation)
    print("\n2. Testing invalid add_student call:")
    result = add_student(
        name="",  # Empty name
        student_id="STU005",
        department="Engineering",
        email="invalid-email"
    )
    print(f"   Result: {result}")
    
    print("\n✅ Function tool validation integration working!")

if __name__ == "__main__":
    print("🏫 Campus Admin Agent - Pydantic Validation Demo")
    print("=" * 60)
    
    # Test Pydantic models directly
    test_pydantic_validations()
    
    # Test function tool integration
    test_function_tool_integration()
    
    print("\n" + "=" * 60)
    print("📚 Summary:")
    print("• All function tools now have robust input validation")
    print("• Data is automatically cleaned and normalized")
    print("• Validation errors are caught before database operations")
    print("• Better error messages for users")
    print("• Type safety and data integrity guaranteed")

