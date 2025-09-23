from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel
from backend.smit_rag import rag_agent
from backend.agent import handoff_agent, student_management_agent, campus_analytics_agent
from memory_store import (
    save_short_term_memory,
    get_short_term_memory,
    save_long_term_memory
)

app = FastAPI()

# Example CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    user_id: str = "user123"   # default if not passed
    thread_id: str = "thread1" # default if not passed


def build_context(user_id: str, thread_id: str, query: str) -> str:
    """Fetch past short-term memory and prepend it to the current query."""
    past_messages = get_short_term_memory(user_id, thread_id, limit=10)
    if not past_messages:
        return query
    context = "\n".join([f"{m['role']}: {m['message']}" for m in past_messages])
    return f"Previous conversation:\n{context}\n\nUser: {query}"


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Load memory
    enhanced_query = build_context(request.user_id, request.thread_id, request.query)

    # Save user input
    save_short_term_memory(request.user_id, request.thread_id, request.query, role="user")

    # Run agent
    result = await Runner.run(handoff_agent, enhanced_query)

    # Extract response
    response_text = str(result.output) if hasattr(result, "output") else str(result)

    # Save agent response
    save_short_term_memory(request.user_id, request.thread_id, response_text, role="assistant")

    return {"response": response_text}


# /chat/stream: Streaming chat responses (SSE)
@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    enhanced_query = build_context(request.user_id, request.thread_id, request.query)
    save_short_term_memory(request.user_id, request.thread_id, request.query, role="user")

    result = Runner.run_streamed(handoff_agent, input=enhanced_query)

    async def event_generator():
        response_text = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                response_text += event.data.delta
                yield event.data.delta

        # Save assistant response after stream ends
        if response_text.strip():
            save_short_term_memory(request.user_id, request.thread_id, response_text, role="assistant")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/students")
async def students(request: ChatRequest):
    result = await Runner.run(student_management_agent, request.query)
    if hasattr(result, "output"):
        return {"response": str(result.output)}
    return {"response": str(result)}


@app.post("/analytics")
async def analytics_endpoint(request: ChatRequest):
    result = await Runner.run(campus_analytics_agent, request.query)
    if hasattr(result, "output"):
        return {"response": str(result.output)}
    return {"response": str(result)}


@app.post("/campus_info_rag")
async def campus_info_endpoint(request: ChatRequest):
    result = await Runner.run(rag_agent, request.query)
    if hasattr(result, "output"):
        return {"response": str(result.output)}
    return {"response": str(result)}


@app.get("/")
async def root():
    return {"message": "Campus Admin Agent API is running."}
