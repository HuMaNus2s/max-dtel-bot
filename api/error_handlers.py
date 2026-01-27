from flask import jsonify, Blueprint
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge
import logging
from os import getenv
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
error_handlers = Blueprint('error_handlers', __name__)

MAX_MESSAGE_LENGTH = getenv("MAX_MESSAGE_LENGTH")

@error_handlers.app_errorhandler(400)
@error_handlers.app_errorhandler(401)
@error_handlers.app_errorhandler(403)
@error_handlers.app_errorhandler(404)
@error_handlers.app_errorhandler(405)
@error_handlers.app_errorhandler(413)
@error_handlers.app_errorhandler(415)
def handle_client_error(error: HTTPException):
    return jsonify({
        "status": "error",
        "code": error.code,
        "message": error.description or "Ошибка запроса"
    }), error.code

@error_handlers.errorhandler(RequestEntityTooLarge)
def handle_too_large(error):
    return jsonify({
        "status": "error",
        "code": 413,
        "message": f"Слишком большой запрос (макс. {MAX_MESSAGE_LENGTH} символов в сообщении)"
    }), 413

@error_handlers.app_errorhandler(502)
def handle_bad_gateway(error: HTTPException):
    """
    Ошибка при попытке отправить сообщение, если сервер не отвечает.
    """
    logger.warning("Ошибка 502: сервер не отвечает при отправке сообщения")
    return jsonify({
        "status": "error",
        "code": 502,
        "message": "Ошибка отправки сообщения в группу: сервер не отвечает"
    }), 502

@error_handlers.app_errorhandler(500)
@error_handlers.app_errorhandler(Exception)
def handle_server_error(error):
    if isinstance(error, HTTPException):
        return error

    logger.exception("Необработанная ошибка в приложении")
    return jsonify({
        "status": "error",
        "code": 500,
        "message": "Внутренняя ошибка сервера"
    }), 500