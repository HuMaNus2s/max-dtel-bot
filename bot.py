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

load_dotenv()
setup_logging(level=logging.DEBUG, log_file="bot.log")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.json.ensure_ascii = False
app.register_blueprint(api_routes, url_prefix='/')

BOT_TOKEN = getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env!")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
dp.include_routers(commands_router_start)

async def shutdown():
    logging.info("Closing bot session")
    try:
        await bot.session.close()
    except Exception as e:
        logging.warning(f"Session close failed: {e}")

def run_flask():
    """Функция для запуска Flask в отдельном потоке"""
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

async def main():
    if not check_db_status():
        logging.warning("Database problems! Check your paths.")
    
    logging.info("BOT STARTING")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("API Server started on http://127.0.0.1:5000")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.exception("Polling error")
    finally:
        await shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        logging.info("BOT STOPPED")