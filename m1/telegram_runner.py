import asyncio
from aiogram import executor
from telegram_bot import dp  # Импортируй откуда у тебя Dispatcher

def start_telegram():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    executor.start_polling(dp, skip_updates=True)
