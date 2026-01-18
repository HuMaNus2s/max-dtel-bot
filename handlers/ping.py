from maxapi import Router, F
from maxapi.types import MessageCreated

router = Router()

@router.message_created(F.message.body.text == "/ping")
async def ping_handler(event: MessageCreated):
    await event.message.answer("pong")