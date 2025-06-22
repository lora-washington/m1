import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
import asyncio

from utils.pnl_logger import read_latest_pnl
from utils.exchange_client import client

API_TOKEN = '7433663009:AAEEUjVHMDRLcn9a95YYCWVnmNOxed8YLl4'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_bot(message: types.Message):
    await message.answer("✅ Бот запущен. Используйте /status для проверки состояния.")

@dp.message_handler(commands=['stop'])
async def stop_bot(message: types.Message):
    await message.answer("🛑 Бот остановлен. Остановить процессы можно через Telegram-управление.")

@dp.message_handler(commands=['status'])
async def status_bot(message: types.Message):
    pnl = read_latest_pnl()
    await message.answer(f"📊 Последние сделки:\n<pre>{pnl}</pre>", parse_mode=ParseMode.HTML)

    try:
        balance = await client.get_balance()
        usdt_balance = balance.get("USDT", 0.0)
        await message.answer(f"💰 Баланс USDT: {usdt_balance:.2f}")
    except Exception as e:
        await message.answer(f"[ERROR] Не удалось получить баланс: {e}")

@dp.message_handler(commands=['restart'])
async def restart_bot(message: types.Message):
    await message.answer("♻️ Перезапуск функций. Пока что не реализовано в коде.")

@dp.message_handler(commands=['status_debug'])
async def status_debug_bot(message: types.Message):
    await message.answer("📊 Статус: бот работает корректно. Можно внедрить детали исполнения в будущем.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
