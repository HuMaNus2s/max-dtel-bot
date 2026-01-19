import httpx
import logging
from os import getenv
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
BOT_TOKEN = getenv("BOT_TOKEN")

async def send_message_to_chat(chat_id: str, text: str, api_base: str = "https://platform-api.max.ru"):
    """
    Функция по отправке сообщения в чат
    """
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing")
        return False, 500

    url = f"{api_base}/messages"
    params = {"chat_id": chat_id}
    headers = {
        "Authorization": BOT_TOKEN,
        "Content-Type": "application/json",
    }
    payload = {"text": text}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers, params=params)
            if response.status_code in (200, 201):
                return True, 201
            else:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return False, 502
    except Exception as e:
        logger.error(f"Network error: {e}")
        return False, 502