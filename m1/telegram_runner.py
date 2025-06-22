import asyncio
from telegram_bot import start_bot  # теперь вызываем асинхронную функцию

def start_telegram():
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
