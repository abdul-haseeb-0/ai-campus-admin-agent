from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel
from backend.agent import handoff_agent, student_management_agent, campus_analytics_agent
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

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    result = await Runner.run(handoff_agent, request.query)
    if hasattr(result, "output"):
        return {"response": str(result.output)}
    return {"response": str(result)}

# /chat/stream: Streaming chat responses (SSE)
@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    result = Runner.run_streamed(handoff_agent, input=request.query)

    async def event_generator():
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                yield event.data.delta

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

@app.get("/")
async def root():
    return {"message": "Campus Admin Agent API is running."}