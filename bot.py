import asyncio
import logging
from os import getenv

from dotenv import load_dotenv

from maxapi import Bot, Dispatcher

from handlers.ping import router as commands_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

BOT_TOKEN = getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env!")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
dp.include_routers(commands_router)


async def shutdown():
    logging.info("Closing bot session")
    try:
        await bot.session.close()
    except Exception as e:
        logging.warning(f"Session close failed: {e}")


async def main():
    logging.info("BOT STARTING")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("Stopped by Ctrl+C")
    except Exception as e:
        logging.exception("Polling error")
    finally:
        await shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopped by Ctrl+C")
    except Exception as e:
        logging.exception("Startup failed")
    finally:
        logging.info("BOT STOPPED")