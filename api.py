import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from core.agent import app as agent_graph

# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="EmerClinic Support API",
    description="Multi-agent support system for EmerClinic — scheduling, billing, FAQ, and operations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    patient_id: Optional[int] = None
    account_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    agent: str


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    thread_id = req.thread_id or str(uuid.uuid4())
    config    = {"configurable": {"thread_id": thread_id}}

    input_state = {
        "messages":         [HumanMessage(content=req.message)],
        "intent":           "",
        "patient_id":       req.patient_id,
        "account_id":       req.account_id,
        "thread_id":        thread_id,
        "current_agent":    "",
        "needs_escalation": False,
        "resolved":         False,
    }

    try:
        result = agent_graph.invoke(input_state, config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    reply = next(
        (
            m.content
            for m in reversed(result["messages"])
            if isinstance(m, AIMessage) and m.content
        ),
        "I'm sorry, I couldn't generate a response.",
    )

    return ChatResponse(
        reply=reply,
        thread_id=thread_id,
        agent=result.get("current_agent", "unknown"),
    )
