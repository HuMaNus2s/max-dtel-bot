import asyncio
import logging
import threading
from os import getenv
from dotenv import load_dotenv
from flask import Flask

from maxapi import Bot, Dispatcher
from handlers.start import router as commands_router_start
from database.database import check_db_status
from logger.logger import setup_logging
from api.routes import api_routes
from api.error_handlers import error_handlers

load_dotenv()
setup_logging(level=logging.DEBUG, log_file="bot.log")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.json.ensure_ascii = False
app.register_blueprint(api_routes, url_prefix='/')
app.register_blueprint(error_handlers)

BOT_TOKEN = getenv("BOT_TOKEN")
HOST_IP = getenv("HOST_IP")
SERVER_PORT = getenv("SERVER_PORT")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env!")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
dp.include_routers(commands_router_start)

async def shutdown():
    logger.info("Closing bot session")
    try:
        await bot.session.close()
    except Exception as e:
        logger.warning(f"Session close failed: {e}")

def run_flask():
    """Функция для запуска Flask в отдельном потоке"""
    app.run(host=HOST_IP, port=SERVER_PORT, debug=False, use_reloader=False)

async def main():
    if not check_db_status():
        logger.warning("Database problems! Check your paths.")
    
    logger.info("BOT STARTING")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"API Server started on http://{HOST_IP}:{SERVER_PORT}")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Error:", e)
    finally:
        await shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("BOT STOPPED")