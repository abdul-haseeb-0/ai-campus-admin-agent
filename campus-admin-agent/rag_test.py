import os
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner
from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel, Field
# from tools import StudentResponse
from dotenv import load_dotenv
import asyncio
# Import all the function tools
from backend.tools import smit_info
from backend.db import get_db, Student, ActivityLog, SessionLocal

load_dotenv()

# ================= initializing LLM ==================

gemini_api_key = os.getenv('GEMINI_API_KEY')

client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# ================= student management agent ==================

campus_info_agent = Agent(
    name="Campus Admin Assistant - Campus Info",
    instructions="""You are a Campus Admin Assistant specialized in providing campus information. You can help with answering questions about campus facilities and services.
    Provide accurate and up-to-date information about campus amenities. don't make up answers. If unsure, say no clearly.
    Always confirm the specific information the user wants before proceeding.""",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[smit_info],
    # output_type=str,
    # tool_choice="required"
)
import asyncio

async def main():
    while True:
        query = input("User: ").strip()
        if query.lower() in {"exit", "quit"}:
            break
        result = await Runner.run(campus_info_agent, query)
        # async for event in result.stream_events():
        #     if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
        #         print(event.data.delta, end="", flush=True)
        print("Assistant:", result.final_output)
        print()

if __name__ == "__main__":
    asyncio.run(main())