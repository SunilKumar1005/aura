from datetime import datetime, timedelta, timezone
import uuid
import aiohttp
import logging
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)

# NoCoDB Auth & Config
NOCO_URL = "https://answermagic.5cn.co.in/api/v1/db/data/noco"
PROJECT_ID = "pq66hsc5sj06r93"
TABLE_ID = "m71ldqche4y4kq9"
VIEW_ID = "vwdme50jau0vmfuq"
AUTH_TOKEN = "TS8euQgxYRS4S14cL3I57wSY2XTT-TwbKjB7fxzt"

HEADERS = {
    "xc-auth": AUTH_TOKEN,
    "Content-Type": "application/json",
    "xc-token": AUTH_TOKEN,
    "accept": "application/json"
}


def parse_nocodb_timestamp(ts: str) -> Optional[datetime]:
    """Parse NoCoDB timestamp to offset-aware datetime object."""
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S%z")
    except ValueError:
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None


async def get_recent_conversations(client_fk: int, hours: int = 24) -> List[Dict]:
    """Get conversations from the last N hours for a client."""
    try:
        if not isinstance(client_fk, int):
            raise ValueError(f"client_fk must be an integer, got {type(client_fk)}")

        time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)

        url = f"{NOCO_URL}/{PROJECT_ID}/{TABLE_ID}/views/{VIEW_ID}?limit=100&offset=0&where=(client_fk,eq,{client_fk})"
        logger.info(f"Fetching conversations for client {client_fk}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS) as response:
                response_text = await response.text()

                if response.status == 200:
                    data = await response.json()
                    conversations = data.get('list', [])

                    filtered = [
                        conv for conv in conversations
                        if (parsed := parse_nocodb_timestamp(conv['timestamp']))
                        and parsed > time_threshold
                    ]

                    filtered.sort(
                        key=lambda x: parse_nocodb_timestamp(x['timestamp']),
                        reverse=True
                    )

                    logger.info(f"Found {len(filtered)} recent conversations for client {client_fk}")
                    return filtered

                elif response.status == 404:
                    logger.info(f"No conversations found for client {client_fk}")
                    return []

                elif response.status == 401:
                    raise Exception("Authentication failed - check AUTH_TOKEN")

                else:
                    logger.error(f"Fetch failed. Status: {response.status}, Response: {response_text}")
                    return []

    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
        return []


async def get_or_create_session(client_fk: str) -> Tuple[str, bool]:
    """Get or create a session for a client. Returns (session_id, is_new_session)"""
    try:
        client_fk_int = int(client_fk)
        conversations = await get_recent_conversations(client_fk_int)

        if conversations:
            last_conversation = conversations[0]
            last_ts = parse_nocodb_timestamp(last_conversation['timestamp'])

            if datetime.now(timezone.utc) - last_ts > timedelta(minutes=20):
                session_id = f"{client_fk}_{uuid.uuid4().hex[:8]}"
                logger.info(f"Creating new session {session_id} (old session expired)")
                return session_id, True
            else:
                session_id = last_conversation['session_id']
                logger.info(f"Using existing session {session_id}")
                return session_id, False

        session_id = f"{client_fk}_{uuid.uuid4().hex[:8]}"
        logger.info(f"No recent session, creating new session {session_id}")
        return session_id, True

    except Exception as e:
        logger.error(f"Session creation error: {str(e)}")
        session_id = f"{client_fk}_{uuid.uuid4().hex[:8]}"
        logger.info(f"Created fallback session {session_id}")
        return session_id, True


async def log_message(
    client_fk: str,
    session_id: str,
    message_source: str,
    message: str,
    intent: str = "",
    entities: dict = None,
    functions: str = "",
    status: str = "",
    prompt: str = ""
) -> bool:
    """Log a message to NoCoDB"""
    try:
        # Ensure client_fk is a string
        client_fk = str(client_fk)

        data = {
            "client_fk": client_fk,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message_source": message_source,
            "message": message,
            "intent": intent,
            "entities": entities or {},
            "functions": functions,
            "status": status,
            "prompt": prompt
        }

        # ✅ POST only to the table endpoint, not views
        url = f"{NOCO_URL}/{PROJECT_ID}/{TABLE_ID}"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=HEADERS, json=data) as response:
                response_text = await response.text()
                if response.status == 200:
                    logger.info(f"✅ Successfully logged message for session {session_id}")
                    return True
                else:
                    logger.error(f"❌ Failed to log message. Status: {response.status}. Response: {response_text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Exception while logging message: {str(e)}")
        return False


async def log_intent_result(
    client_fk: str,
    session_id: str,
    message: str,
    intent: str,
    functions: List[str] = [],
    entities: dict = {},
    status: str = "",
    message_source: str = "intent_bot",
    prompt: str = ""
):
    """Helper to log intent detection result."""
    await log_message(
        client_fk=client_fk,
        session_id=session_id,
        message_source=message_source,
        message=message,
        intent=intent,
        entities=entities,
        functions=", ".join(functions),
        status=status
    )
