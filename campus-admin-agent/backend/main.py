import uuid
from fastapi import FastAPI, HTTPException
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
    save_long_term_memory,
    clear_short_term_memory,
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
    user_id: str | None = None
    thread_id: str | None = None


def get_ids(request: ChatRequest):
    """Ensure user_id and thread_id exist, else generate UUIDs."""
    user_id = request.user_id or str(uuid.uuid4())
    thread_id = request.thread_id or str(uuid.uuid4())
    return user_id, thread_id


def build_context(user_id: str, thread_id: str, query: str) -> str:
    """Fetch past short-term memory and prepend it to the current query."""
    try:
        past_messages = get_short_term_memory(user_id, thread_id, limit=10)
    except Exception as e:
        past_messages = []
        print(f"[Memory Error] Failed to fetch short-term memory: {e}")

    if not past_messages:
        return query
    context = "\n".join([f"{m['role']}: {m['message']}" for m in past_messages])
    return f"Previous conversation:\n{context}\n\nUser: {query}"


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_id, thread_id = get_ids(request)

    # Save user input
    try:
        save_short_term_memory(user_id, thread_id, request.query, role="user")
    except Exception as e:
        print(f"[Memory Error] Failed to save user message: {e}")

    # Build context + run agent
    enhanced_query = build_context(user_id, thread_id, request.query)
    try:
        result = await Runner.run(handoff_agent, enhanced_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    # Extract response
    response_text = str(result.output) if hasattr(result, "output") else str(result)

    # Save assistant response
    try:
        save_short_term_memory(user_id, thread_id, response_text, role="assistant")
    except Exception as e:
        print(f"[Memory Error] Failed to save assistant response: {e}")

    return {"response": response_text, "user_id": user_id, "thread_id": thread_id}


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    user_id, thread_id = get_ids(request)

    try:
        save_short_term_memory(user_id, thread_id, request.query, role="user")
    except Exception as e:
        print(f"[Memory Error] Failed to save user message: {e}")

    enhanced_query = build_context(user_id, thread_id, request.query)
    result = Runner.run_streamed(handoff_agent, input=enhanced_query)

    async def event_generator():
        response_text = ""
        try:
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    response_text += event.data.delta
                    yield event.data.delta
        except Exception as e:
            print(f"[Stream Error] {e}")
            yield f"\n[Error streaming response: {e}]"

        # Save assistant response after stream ends
        if response_text.strip():
            try:
                save_short_term_memory(user_id, thread_id, response_text, role="assistant")
            except Exception as e:
                print(f"[Memory Error] Failed to save assistant response: {e}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/end_thread")
async def end_thread(request: ChatRequest):
    user_id, thread_id = get_ids(request)
    try:
        past_messages = get_short_term_memory(user_id, thread_id, limit=50)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory fetch error: {e}")

    if not past_messages:
        return {"message": "No conversation found to summarize."}

    convo_text = "\n".join([f"{m['role']}: {m['message']}" for m in past_messages])
    summary_prompt = f"Summarize the following conversation in 5 sentences, focusing on important details:\n\n{convo_text}"

    try:
        result = await Runner.run(handoff_agent, summary_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error during summary: {e}")

    summary = str(result.output) if hasattr(result, "output") else str(result)

    try:
        save_long_term_memory(user_id, summary, tags=["thread_summary"])
        clear_short_term_memory(user_id, thread_id)
    except Exception as e:
        print(f"[Memory Error] Failed to save long-term memory: {e}")

    return {
        "message": "Thread summarized and saved to long-term memory.",
        "summary": summary,
        "user_id": user_id,
        "thread_id": thread_id,
    }


@app.post("/students")
async def students(request: ChatRequest):
    result = await Runner.run(student_management_agent, request.query)
    return {"response": str(result.output) if hasattr(result, "output") else str(result)}


@app.post("/analytics")
async def analytics_endpoint(request: ChatRequest):
    result = await Runner.run(campus_analytics_agent, request.query)
    return {"response": str(result.output) if hasattr(result, "output") else str(result)}


@app.post("/campus_info_rag")
async def campus_info_endpoint(request: ChatRequest):
    result = await Runner.run(rag_agent, request.query)
    return {"response": str(result.output) if hasattr(result, "output") else str(result)}


@app.get("/")
async def root():
    return {"message": "Campus Admin Agent API is running."} 