from maxapi import Router
from maxapi.types import MessageCreated, Command

router = Router()

@router.message_created(Command("start"))
async def start_handler(event: MessageCreated):
    await event.message.answer(f"Привет! Это бот для рассылки сообщений в группы")