import os
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, handoffs
from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel, Field
from tools import StudentResponse
from dotenv import load_dotenv
import asyncio

# Import all the function tools
from tools import (
    add_student, get_student, update_student, delete_student, list_students,
    get_total_students, get_students_by_department, get_recent_onboarded_students,
    get_active_students_last_7_days, get_cafeteria_timings, get_library_hours
)

load_dotenv()

# ================= initializing LLM ==================

gemini_api_key = os.getenv('GEMINI_API_KEY')

client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)



# ================= student management agent ==================
# 📌 Student Management Agent
# function tootls from tools.py:
# ● add_student(name, id, department, email)
# ● get_student(id)
# ● update_student(id, field, new_value)
# ● delete_student(id)
# ● list_students()

student_management_agent = Agent(
    name="Campus Admin Assistant - Student Management",
    instructions="""You are a Campus Admin Assistant specialized in managing student records. You can help with adding, retrieving, updating, deleting, and listing student information.
    Always confirm actions that modify data (add, update, delete) with the user before proceeding.
    Ensure student IDs and emails are unique when adding new students.
    Provide clear feedback on the success or failure of operations.""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[
        add_student,
        get_student,
        update_student,
        delete_student,
        list_students,
    ],
    output_type=StudentResponse
)

# ================= campus analytics agent ==================
# 📌 Campus Analytics agent
# function tools from tools.py:
# - Get total student counts (active/inactive breakdown)
# - View student distribution by department
# - Find recently onboarded students
# - Track students active in the last 7 days

campus_analytics_agent = Agent(
    name="Campus Admin Assistant - Campus Analytics",
    instructions="""You are a Campus Admin Assistant specialized in campus analytics. You can help with retrieving student statistics and insights.
    Provide clear and concise summaries of the requested analytics data.
    Always confirm the specific analytics the user wants before proceeding.""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[
        get_total_students,
        get_students_by_department,
        get_recent_onboarded_students,
        get_active_students_last_7_days,
    ],
)
    # output_type=str,
print("Campus Analytics Agent initialized.")

# ================= campus info agent ==================
# 📌 Campus FAQ agent
# function tools from tools.py:
# - Provide cafeteria operating hours
# - Share library hours and study room access information

campus_info_agent = Agent(
    name="Campus Admin Assistant - Campus Info",
    instructions="""You are a Campus Admin Assistant specialized in providing campus information. You can help with answering questions about campus facilities and services.
    Provide accurate and up-to-date information about campus amenities. don't make up answers. If unsure, say no clearly.
    Always confirm the specific information the user wants before proceeding.""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[
        get_cafeteria_timings, 
        get_library_hours
    ],
    output_type=str,
    # tool_choice="required"
)
print("Campus Info Agent initialized.")

# ================= combined agent ==================
handoff_agent = Agent(
    name="Campus Admin Assistant - Handoff Agent",
    instructions="""You are a Campus Admin Assistant that can handle a wide range of queries related to student management, campus analytics, and campus information. Based on the user's query, you will determine which specialized agent (Student Management, Campus Analytics, or Campus Info) is best suited to handle the request.
    you will handoff the query to the appropriate agent based on the user's needs.
    Agents available:
    • Student Management: add_student, get_student, update_student, delete_student, list_students
    • Analytics: get_total_students, get_students_by_department, get_recent_onboarded_students, get_active_students_last_7_days
    • Campus Info: get_cafeteria_timings, get_library_hours
    Your goal is to ensure the user gets the most accurate and relevant information or assistance possible. Always aim to
    """,
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    handoffs=[student_management_agent, campus_analytics_agent, campus_info_agent],
)
print("Handoff Agent initialized.")


# be helpful, accurate, and provide clear responses. When working with student data, ensure you handle errors gracefully and provide meaningful feedback to users.""",
async def main():
    print("🏫 Campus Admin Assistant")
    print("=" * 50)
    print("Available functions:")
    print("• Student Management: add_student, get_student, update_student, delete_student, list_students")
    print("• Analytics: get_total_students, get_students_by_department, get_recent_onboarded_students, get_active_students_last_7_days")
    print("• Campus Info: get_cafeteria_timings, get_library_hours")
    print("=" * 50)
    
    while True:
        query = input("\n💬 Enter your query (or 'quit' to exit): ")
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        print("\n🤖 Assistant:")
        result = Runner.run_streamed(handoff_agent, input=query)
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
        print()  # Add newline after response


if __name__ == "__main__":
    asyncio.run(main())   