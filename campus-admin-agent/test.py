from backend.config.llm import get_llm
import os
from agents import Agent, Runner

import asyncio
model = get_llm()

agent = Agent(
    name="assistant",
    instructions="You are a helpful campus admin assistant. Use the tools below to assist with student management tasks.",
    model=model,
)

query = input("Enter your query: ")
response = Runner.run(
    agent=agent,
    query=query,)

print("Response:", response.final_output)
