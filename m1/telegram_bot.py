import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from utils.pnl_logger import read_latest_pnl
from utils.exchange_client import client
import asyncio

API_TOKEN = '7433663009:AAEEUjVHMDRLcn9a95YYCWVnmNOxed8YLl4'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_bot(message: types.Message):
    await message.answer("✅ Бот запущен. Управление активностью доступно через Telegram-команды.")

@dp.message_handler(commands=['stop'])
async def stop_bot(message: types.Message):
    try:
        from websocket import momentum_ws_bot
        if hasattr(momentum_ws_bot, 'active_bot') and momentum_ws_bot.active_bot:
            momentum_ws_bot.active_bot.stop()
            await message.answer("🛑 Бот остановлен. Остановить процессы можно через Telegram-управление.")
        else:
            await message.answer("ℹ️ Бот не был активен.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при остановке бота: {e}")

@dp.message_handler(commands=['status_debug'])
async def status_debug_bot(message: types.Message):
    await message.answer("📊 Статус: все работает. Можно внедрить информацию о ценах, позициях и PnL.")

@dp.message_handler(commands=['restart'])
async def restart_bot(message: types.Message):
    await message.answer("♻️ Перезапуск... Поддержка реализуется в логике бота.")

@dp.message_handler(commands=['status'])
async def status_bot(message: types.Message):
    try:
        pnl = read_latest_pnl()
        await message.answer(f"📊 Последние сделки:\n<pre>{pnl}</pre>", parse_mode=ParseMode.HTML)
    except Exception:
        await message.answer("📊 Последние сделки:\n<pre>No trades yet</pre>", parse_mode=ParseMode.HTML)

    try:
        balance = await client.get_balance()
        usdt = balance.get("USDT", 0)
        await message.answer(f"💰 Баланс USDT: {usdt:.2f}")
    except Exception as e:
        await message.answer(f"❌ Ошибка получения баланса: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
