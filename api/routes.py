from __future__ import annotations

import logging
from os import getenv
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request, current_app, abort

from .sender import send_message_to_chat
from database.database import Database, check_db_status

load_dotenv()

logger = logging.getLogger(__name__)

api_routes = Blueprint('api', __name__)

MAX_MESSAGE_LENGTH = getenv("MAX_MESSAGE_LENGTH")

@api_routes.get("/health")
def health_check():
    """
    Проверка состояния сервиса
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
    last_update = current_app.config.get("last_successful_update", now)
    delta = now - last_update

    status = "online"
    details: Dict[str, str] = {}

    if delta > timedelta(minutes=3):
        status = "pending"

    try:
        check_db_status()
        details["database"] = "ok"
    except Exception as exc:
        logger.exception("Проверка БД упала")
        status = "offline"
        details["database"] = f"error: {type(exc).__name__}"

    payload = {
        "status": status,
        "run_time_seconds": round(delta.total_seconds(), 1),
        "details": details,
        "timestamp_utc": now.isoformat(),
    }

    code = 200 if status in ("online", "pending") else 503
    return jsonify(payload), code


@api_routes.post("/send")
async def send_message():
    """
    Отправка сообщения в группу чатов
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
    
    Ожидаемый JSON:
    {
      "group_name": str,
      "message": str (макс. 4096 символов),
      "api_key": str
    }
    """
    if not request.is_json:
        abort(415, description="Ожидается Content-Type: application/json")

    data = request.get_json() or {}

    group_name = data.get("group_name")
    message   = data.get("message")
    api_key   = data.get("api_key")

    if not all([group_name, message, api_key]):
        abort(400, description="Отсутствет обязательное поле")

    if not isinstance(message, str):
        abort(400, description="Поле message должно быть строкой")

    if len(message) > MAX_MESSAGE_LENGTH:
        abort(413, description=f"Сообщение слишком длинное (макс. {MAX_MESSAGE_LENGTH} символов)")

    if not message.strip():
        abort(400, description="Поле message не может быть пустым")

    if not Database.is_key_allowed_for_group(api_key, group_name):
        abort(401, description="Неверный ключ доступа для отправки")

    chat_ids: List[int] = Database.get_chat_ids_for_group(group_name)

    if not chat_ids:
        logger.info("Группа %s пуста — нет чатов", group_name)
        return jsonify({
            "status": "ok",
            "sent_to": [],
            "message": "В группе нет активных чатов"
        }), 200

    sent_to: List[str] = []
    failed:  List[Dict[str, Any]] = []

    for chat_id in chat_ids:
        try:
            ok, err = await send_message_to_chat(chat_id=chat_id, text=message)
            if ok:
                sent_to.append(str(chat_id))
            else:
                if err and "server" in str(err).lower():
                    abort(502, description="Ошибка отправки сообщения в группу: сервер не отвечает")

                failed.append({"chat_id": str(chat_id), "reason": err or "неизвестная ошибка"})
        except Exception as e:
            logger.exception("Ошибка отправки в чат %s", chat_id)

            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                abort(502, description="Ошибка отправки сообщения в группу: сервер не отвечает")

            failed.append({"chat_id": str(chat_id), "reason": "внутренняя ошибка"})

    status = "success" if sent_to and not failed else "partial" if sent_to else "failed"
    code   = 201 if status == "success" else 207 if status == "partial" else 200

    return jsonify({
        "status": status,
        "sent_to": sent_to,
        "failed": failed or None,
        "total_target": len(chat_ids),
    }), code