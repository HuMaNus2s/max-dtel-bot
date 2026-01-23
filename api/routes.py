from flask import Blueprint, request, jsonify, abort
from .sender import send_message_to_chat
from datetime import datetime, timedelta, timezone
from database.database import check_db_status
from database.database import Database

import logging
logger = logging.getLogger(__name__)

MAX_LENGTH_MESSAGE = 4096

api_routes = Blueprint('api', __name__)
last_successful_update = datetime.now(timezone.utc)

@api_routes.route("/health", methods=["GET"])
def get_health():
    """
    Роут отправляет состояние бота
    #### Состояния:
    - online: Бот в сети
    - pending: Неактивен уже 3 минуты(На паузе)
    - offline: Бот не в сети
    #### Успех:
    - 200: Отправлено состояние
    #### Errors:
    - 503: Бот не в сети или в ожидании 
    """
    now = datetime.now(timezone.utc)
    time_since_last_update = now - last_successful_update
    
    status = "online"
    details = {}
    
    if time_since_last_update > timedelta(minutes=3):
        status = "pending"
    
    try:
        check_db_status()
        details["database"] = "ok"
    except Exception:
        status = "offline"
        details["database"] = "error"
    
    return jsonify({
        "status": status,
        "run_time": f"{time_since_last_update.total_seconds():.1f}s",
        "details": details,
        "timestamp": now.isoformat()
    }), 200 if status == "online" or status == "pending" else 503

@api_routes.route("/send", methods=["POST"])
async def send_route():
    """
    Роут для отправки сообщения в чат
    #### Args:
    - group_name: Мнемоническое имя группы (String)
    - message: Отправляемое сообщение (String | Max.chars: 4096)
    - api_key: ключ доступа (String)
    #### Успех:
    - 201: Сообщение отправлено
    #### Errors:
    - 400: Отсутствет обязательное поле
    - 401: Неверный ключ доступа для отправки
    - 413: Текст слишком длинный (макс. 4096 символов)
    """
    data = request.get_json() or {}
    check_db_status()
    
    group_name = data.get('group_name')
    message = data.get('message')
    api_key = data.get('api_key')

    if not all([group_name, message, api_key]):
        return jsonify({
            "status": "error",
            "code": 400,
            "message": "Отсутствет обязательное поле"
        }), 400

    if not Database.is_key_allowed_for_group(api_key, group_name):
        return jsonify({
            "status": "error",
            "code": 401,
            "message": "Неверный ключ доступа для отправки"
        }), 401
    
    if len(message) > MAX_LENGTH_MESSAGE:
        return jsonify({
            "status": "error",
            "code": 413,
            "message": f"Текст слишком длинный (макс. {MAX_LENGTH_MESSAGE} символов)"
        }), 413

    chat_ids = Database.get_chat_ids_for_group(group_name)
    sent_ids = []
    
    for c_id in chat_ids:
        success, _ = await send_message_to_chat(chat_id=c_id, text=message)
        if success:
            sent_ids.append(str(c_id))

    return jsonify({
        "status": "success",
        "sent_to": sent_ids,
        "message": "Сообщение отправлено"
    }), 201