# api.py
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
# from chat_engine import run_chat_pipeline
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response
import asyncio
from llm_handler.chat_engine import run_chat_pipeline
import aiohttp
import requests
from datetime import datetime, timedelta
import uuid
from typing import Optional, List
import logging
from nocodb_handler import get_recent_conversations, get_or_create_session, log_message
from fastapi import APIRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend origin in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NoCoDB Auth & Config
NOCO_URL = "https://answermagic.5cn.co.in/api/v1/db/data/noco"
PROJECT_ID = "pq66hsc5sj06r93"
TABLE_ID = "m71ldqche4y4kq9"  # conversation_logs
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InN1bmlsLmt1bWFyQDVjbmV0d29yay5jb20iLCJpZCI6InVzMW9hYnV4bjZjYjN3NjAiLCJyb2xlcyI6eyJvcmctbGV2ZWwtY3JlYXRvciI6dHJ1ZX0sInRva2VuX3ZlcnNpb24iOiJhNzVhYTBiMGU4YWEwYzA2NjdhZjA1ODUzZTRlNWE0N2I2MWY5NzNiMmIyYTYwNjJkNGY3ZTIyY2Q4ZjNkZDEwOGM5M2RjMjIyYzdjZTQ4MCIsImlhdCI6MTc0OTk3MDkxNCwiZXhwIjoxNzUwMDA2OTE0fQ.OriqtU-oq8ldT21GYcjRgC8sBVhEdJsWNysCw23CexM"

HEADERS = {
    "xc-auth": AUTH_TOKEN,
    "Content-Type": "application/json"
}

class ChatRequest(BaseModel):
    user_id: str  # For future context tracking
    client_id: int  # Hospital or diagnostic center
    message: str
    session_id: Optional[str] = None  # Optional session ID for continuing conversations

class ConversationLog(BaseModel):
    client_fk: str
    message_source: str  # user, intent_bot, response_bot
    message: str
    intent: str | None = None
    entities: dict | None = None
    functions: str | None = None

class ConversationHistory(BaseModel):
    session_id: str
    client_fk: str
    timestamp: str
    message_source: str
    message: str
    intent: Optional[str] = None
    entities: Optional[dict] = None
    functions: Optional[str] = None

async def log_message_async(client_fk: str, session_id: str, message_source: str, message: str, 
                          intent: Optional[str] = None, entities: Optional[dict] = None, 
                          functions: Optional[str] = None):
    """Asynchronous function to log messages to NoCoDB"""
    try:
        data = {
            "client_fk": client_fk,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message_source": message_source,
            "message": message,
            "intent": intent,
            "entities": entities,
            "functions": functions
        }
        
        url = f"{NOCO_URL}/{PROJECT_ID}/{TABLE_ID}/rows"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=HEADERS, json=data) as response:
                if response.status != 200:
                    logger.error(f"Failed to log message: {await response.text()}")
    except Exception as e:
        logger.error(f"Error logging message to NoCoDB: {str(e)}")

async def get_last_log_async(client_fk: str) -> Optional[dict]:
    """Asynchronous function to get the last log from NoCoDB"""
    try:
        url = f"{NOCO_URL}/{PROJECT_ID}/{TABLE_ID}/rows?limit=1&where=(client_fk,eq,{client_fk})&sort=-timestamp"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS) as response:
                if response.status == 200:
                    data = await response.json()
                    rows = data.get('list', [])
                    return rows[0] if rows else None
                else:
                    logger.error(f"Failed to get last log: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Error getting last log from NoCoDB: {str(e)}")
        return None

@app.get("/conversation/{client_fk}", response_model=List[ConversationHistory])
async def get_conversation_history(client_fk: str, session_id: Optional[str] = None):
    try:
        # If no session_id provided or session is old, create new session
        if not session_id:
            last_log = await get_last_log_async(client_fk)
            if last_log:
                last_ts = datetime.fromisoformat(last_log['timestamp'])
                if datetime.utcnow() - last_ts <= timedelta(minutes=20):
                    session_id = last_log['session_id']
                else:
                    session_id = f"{client_fk}_{uuid.uuid4().hex[:8]}"
            else:
                session_id = f"{client_fk}_{uuid.uuid4().hex[:8]}"
        
        # Fetch conversation history for the session
        url = f"{NOCO_URL}/{PROJECT_ID}/{TABLE_ID}/rows?where=(session_id,eq,{session_id})&sort=timestamp"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('list', [])
                else:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to fetch conversation history: {await response.text()}"
                    )
    except Exception as e:
        logger.error(f"Error fetching conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def prepare_conversation_for_llm(conversations: list) -> list:
    """
    Convert NoCoDB conversation records to LLM-friendly format.
    Example output: [{"role": "user", "content": "hi"}, {"role": "bot", "content": "hello"}]
    """
    formatted = []
    for conv in conversations:
        role = "user" if conv.get("message_source") == "user" else "bot"
        formatted.append({
            "role": role,
            "content": conv.get("message", "")
        })
    return formatted

@app.post("/chat/stream")
async def chat_endpoint(request: ChatRequest):
    try:
        # Convert client_id to integer and validate
        try:
            client_fk = int(request.client_id)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid client_id: {request.client_id}")
            return Response(content="", media_type="text/html")
            
        conversations = []  # Initialize empty list for conversation history
        
        # Step 1: Get recent conversations and session info
        try:
            conversations = await get_recent_conversations(client_fk)
            session_id, is_new_session = await get_or_create_session(str(client_fk))  # Convert to string for session ID
            if conversations:
                conversations.sort(key=lambda x: x.get('timestamp', ''))
        except Exception as e:
            logger.error(f"Failed to get conversation history: {str(e)}")
            # Create a new session even if history fetch fails
            session_id = f"{client_fk}_{uuid.uuid4().hex[:8]}"

        # Step 2: Log the user message immediately
        try:
            await log_message(
                client_fk=str(client_fk),  # Convert to string for logging
                session_id=session_id,
                message_source="user",
                message=request.message
            )
        except Exception as e:
            logger.error(f"Failed to log user message: {str(e)}")
            return Response(content="", media_type="text/html")

        # Step 3: Prepare conversation history for LLM
        structured_history = prepare_conversation_for_llm(conversations)

        # Step 4: Call the LLM pipeline (intent detection, etc.)
        try:
            llm_stream = await run_chat_pipeline(
                user_id=request.user_id,
                client_id=request.client_id,
                user_message=request.message,
                conversation_history=structured_history,
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"LLM pipeline error: {str(e)}")
            return Response(content="", media_type="text/html")

        # Stream the LLM response directly to the UI
        return StreamingResponse(llm_stream, media_type="text/html")

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return Response(content="", media_type="text/html")

def split_html_for_streaming(html_text, chunk_size=50):
    for i in range(0, len(html_text), chunk_size):
        yield html_text[i:i + chunk_size]

@app.post("/log")
async def log_conversation(entry: ConversationLog):
    now = datetime.utcnow().isoformat()
    last = await get_last_log_async(entry.client_fk)
    
    # Session ID logic
    if last:
        last_ts = datetime.fromisoformat(last['timestamp'])
        if datetime.utcnow() - last_ts > timedelta(minutes=20):
            session_id = f"{entry.client_fk}_{uuid.uuid4().hex[:8]}"
        else:
            session_id = last['session_id']
    else:
        session_id = f"{entry.client_fk}_{uuid.uuid4().hex[:8]}"
        print(f"New session ID: {session_id}")
    
    data = {
        "client_fk": entry.client_fk,
        "session_id": session_id,
        "timestamp": now,
        "message_source": entry.message_source,
        "message": entry.message,
        "intent": entry.intent,
        "entities": entry.entities,
        "functions": entry.functions
    }
    print(f"Data: {data}")
    url = f"{NOCO_URL}/{PROJECT_ID}/{TABLE_ID}/rows"
    res = requests.post(url, headers=HEADERS, json=data)

    if res.status_code == 200:
        return {"status": "success", "session_id": session_id}
    else:
        raise HTTPException(status_code=res.status_code, detail=res.text)


