#!/usr/bin/env python3
"""
Test script for Campus Admin Agent with Function Tools
This script demonstrates how the OpenAI Agent SDK function tools work
"""

import asyncio
import os
from dotenv import load_dotenv
from backend.agent import main

def test_function_tools():
    """Test the function tools directly"""
    print("🧪 Testing Function Tools Directly")
    print("=" * 50)
    
    # Import the tools
    from backend.tools import (
        add_student, get_student, list_students, 
        get_total_students, get_cafeteria_timings
    )
    
    # Test cafeteria timings (no DB required)
    print("\n1. Testing get_cafeteria_timings():")
    result = get_cafeteria_timings()
    print(f"   Result: {result}")
    
    # Test library hours (no DB required)
    from backend.tools import get_library_hours
    print("\n2. Testing get_library_hours():")
    result = get_library_hours()
    print(f"   Result: {result}")
    
    print("\n✅ Function tools are working!")
    print("💡 Note: Database-dependent functions require a valid DATABASE_URL")

def run_agent():
    """Run the interactive agent"""
    print("\n🚀 Starting Campus Admin Agent...")
    print("Make sure you have:")
    print("• GEMINI_API_KEY set in your .env file")
    print("• DATABASE_URL set in your .env file (for database operations)")
    print("• Database tables created (run backend/db.py)")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Error running agent: {e}")
        print("💡 Check your .env file and database connection")

if __name__ == "__main__":
    load_dotenv()
    
    print("🏫 Campus Admin Agent - Function Tools Demo")
    print("=" * 60)
    
    # Test function tools first
    test_function_tools()
    
    # Ask user if they want to run the interactive agent
    print("\n" + "=" * 60)
    choice = input("Would you like to run the interactive agent? (y/n): ")
    
    if choice.lower() in ['y', 'yes']:
        run_agent()
    else:
        print("👋 Demo complete! Run 'python backend/agent.py' to start the agent.")
