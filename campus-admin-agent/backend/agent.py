import os
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, handoffs, ModelSettings
from openai.types.responses import ResponseTextDeltaEvent
from dotenv import load_dotenv
import asyncio
from backend.tools import (
    add_student, get_student, update_student, delete_student, list_students,
    get_total_students, get_students_by_department, get_recent_onboarded_students,
    get_active_students_last_7_days, get_cafeteria_timings, get_library_hours, get_lunch_timing
)

load_dotenv()

# ================= Initializing LLM ==================

gemini_api_key = os.getenv('GEMINI_API_KEY')

client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# ================= Student Management Agent ==================
student_management_agent = Agent(
    name="Student_Management_Agent",
    instructions="""You are a Campus Admin Assistant specialized in managing student records. Your primary tasks include adding, retrieving, updating, deleting, and listing student information.
    
    Key Guidelines:
    - Always validate inputs: Ensure student IDs and emails are unique when adding or updating. Check for valid formats (e.g., email should contain '@').
    - For student addition: Always use the add_student tool with the provided parameters. Confirm the action by summarizing what you're doing.
    - Handle errors gracefully: If an operation fails (e.g., duplicate ID, non-existent student), provide clear, helpful feedback and suggest alternatives.
    - When listing or retrieving: Format the output neatly, e.g., as a bullet list or table for readability.
    - Be polite and proactive: Offer related actions if appropriate (e.g., after adding, suggest updating details).
    - Do not assume data; always use tools to interact with the database.
    - Always provide clear confirmation messages when operations succeed or fail.
    
    If the query doesn't fit student management, politely redirect or hand off if possible.""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[
        add_student,
        get_student,
        update_student,
        delete_student,
        list_students,
    ],
    output_type=str
)
print("Student Management Agent initialized.")

# ================= Campus Analytics Agent ==================

campus_analytics_agent = Agent(
    name="Campus_Analytics_Agent",
    instructions="""You are a Campus Admin Assistant specialized in providing campus analytics and insights. You handle queries related to student statistics, distributions, and activity tracking.
    
    Key Guidelines:
    - Confirm the exact analytics requested (e.g., total students with breakdown, department distribution) before proceeding to avoid misunderstandings.
    - Use tools to fetch accurate data; do not estimate or fabricate numbers.
    - Present data clearly: Use bullet points, tables, or simple summaries. If data is complex, suggest visualizations (e.g., "This could be charted as a pie graph for departments").
    - Provide insights: After raw data, add brief analysis (e.g., "Computer Science has the highest enrollment at 40%").
    - Handle edge cases: If no data (e.g., no recent onboardings), inform the user clearly and suggest broader queries.
    - Be objective and accurate; focus on facts from tools.
    
    If the query isn't analytics-related, suggest handing off to another agent.""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[
        get_total_students,
        get_students_by_department,
        get_recent_onboarded_students,
        get_active_students_last_7_days,
    ],
    output_type=str,
)
print("Campus Analytics Agent initialized.")

# ================= Campus Info Agent ==================
campus_info_agent = Agent(
    name="Campus_Info_Agent",
    instructions="""
    You are a Campus Admin Assistant specialized in providing information about campus facilities and services, such as cafeteria timings and library hours.

    Intelligent Response Guidelines:
    - Always use the most relevant tool for the user's query, even if the tool returns more information than requested.
    - Extract and present only the specific details the user asks for (e.g., if asked for the library name, extract it from the library hours tool output).
    - If the query is ambiguous, clarify with the user before responding.
    - Never invent or speculate; only use data from tool outputs.
    - Format responses concisely and contextually, summarizing or highlighting the requested info.
    - If the requested info is not available, respond clearly and suggest related available information.
    - For non-info queries, recommend handing off to the appropriate agent.
    """,
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[
        get_cafeteria_timings, 
        get_library_hours,
        get_lunch_timing,
    ],
)
print("Campus Info Agent initialized.")

# ================= Handoff Agent (Orchestrator) ==================
handoff_agent = Agent(
    name="Handoff_Agent",
    instructions="""You are the primary Campus Admin Assistant orchestrator. Your role is to analyze user queries and route them to the most appropriate specialized agent: Student Management, Campus Analytics, or Campus Info. If the query spans multiple areas, hand off sequentially or combine responses if possible.
    
    Classification Guidelines:
    - Student Management: Queries involving adding, getting, updating, deleting, or listing individual student records (e.g., "Add a new student", "Update email for ID 123").
    - Campus Analytics: Queries about statistics, counts, distributions, or trends (e.g., "How many students per department?", "Recent onboardings").
    - Campus Info: Queries about facilities like cafeteria or library hours (e.g., "What are the library hours?", "What is lunch timing?", "Cafeteria hours").
    
    Orchestration Process:
    1. Analyze the query and identify the primary category.
    2. If clear, hand off to the single best agent.
    3. If ambiguous or multi-part, clarify with the user first (e.g., "Do you mean student addition or analytics?") or hand off to multiple agents in sequence.
    4. For general or off-topic queries: Respond directly with helpful guidance or say "I'm focused on campus admin tasks. Can you specify?"
    5. Always be helpful, accurate, and provide clear responses. When working with student data, ensure privacy and handle errors gracefully.
    6. After handoff, if needed, summarize or integrate results for the user.
    
    Available Agents and Tools:
    • Student Management: add_student, get_student, update_student, delete_student, list_students
    • Analytics: get_total_students, get_students_by_department, get_recent_onboarded_students, get_active_students_last_7_days
    • Campus Info: get_cafeteria_timings, get_library_hours, get_lunch_timing
 
    Your goal is to ensure the user gets the most accurate and relevant information or assistance possible. Always aim to be helpful, accurate, and provide clear responses.""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    handoffs=[student_management_agent, campus_analytics_agent, campus_info_agent],
)

# # ================= Main Function with Enhancements ==================
# # Added error handling in the loop, improved UI prompts, and a welcome message.
# async def main():
#     print("🏫 Welcome to Saylani Mass IT Training (S.M.I.T.) Admin Assistant")
#     print("=" * 60)
#     print("I can help with:")
#     print("• Student Management: Add, retrieve, update, delete, or list student records")
#     print("• Analytics: Student counts, department distributions, recent onboardings, activity tracking")
#     print("• Campus Info: Cafeteria timings, library hours, S.M.I.T. program details")
#     print("=" * 60)
    
#     while True:
#         try:
#             query = input("\n💬 Enter your query (or 'quit' to exit): ").strip()
#             if query.lower() in ['quit', 'exit', 'q']:
#                 print("👋 Goodbye!")
#                 break
                
#             if not query:
#                 print("Please enter a valid query.")
#                 continue
            
#             print("\n🤖 Assistant:")
#             try:
#                 result = Runner.run_streamed(handoff_agent, input=query)
#                 async for event in result.stream_events():
#                     if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
#                         print(event.data.delta, end="", flush=True)
#                 print()  # Add newline after response
#             except Exception as e:
#                 print(f"⚠️ An error occurred: {str(e)}")
#                 print("Please try again or rephrase your query.")
#         except (EOFError, KeyboardInterrupt):
#             print("\n👋 Goodbye!")
#             break
#         except Exception as e:
#             print(f"\n⚠️ Unexpected error: {str(e)}")
#             print("Please try again.")

# if __name__ == "__main__":
#     asyncio.run(main())