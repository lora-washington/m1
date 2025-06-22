import asyncio
from aiogram import executor, types
from telegram_bot import dp, bot  # Импортируем Dispatcher и Bot
from bots.grid_ws_bot import GridBot
from bots.momentum_ws_bot import MomentumBot
import json

# Загружаем API и конфиг
with open("config.json") as f:
    config = json.load(f)

API_KEY = config["API_KEY"]
API_SECRET = config["API_SECRET"]
PAIRS = config["PAIRS"]
GRID_CFG = config["grid"]
MOMENTUM_CFG = config["momentum"]

running_bots = []  # Здесь будут храниться все запущенные боты

@dp.message_handler(commands=['start'])
async def start_bots(message: types.Message):
    if running_bots:
        await message.answer("⚠️ Боты уже запущены.")
        return

    await message.answer("🚀 Запуск ботов...")

    for symbol in PAIRS:
        grid_bot = GridBot(API_KEY, API_SECRET, symbol, **GRID_CFG)
        momentum_bot = MomentumBot(API_KEY, API_SECRET, symbol, **MOMENTUM_CFG)
        running_bots.append(grid_bot)
        running_bots.append(momentum_bot)

        asyncio.create_task(grid_bot.start())
        asyncio.create_task(momentum_bot.start())

    await message.answer("✅ Все боты запущены.")

@dp.message_handler(commands=['stop'])
async def stop_bots(message: types.Message):
    if not running_bots:
        await message.answer("⛔️ Боты уже остановлены.")
        return

    for bot_instance in running_bots:
        bot_instance.stop()

    running_bots.clear()

    await message.answer("🛑 Боты остановлены.")

@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    from utils.pnl_logger import read_latest_pnl
    from utils.exchange_client import client

    pnl = read_latest_pnl()
    await message.answer(f"📊 Последние сделки:\n<pre>{pnl}</pre>", parse_mode="HTML")

    balance = await client.get_balance()
    await message.answer(f"💰 Баланс USDT: {balance.get('USDT', 0)}")

# Запуск Telegram-бота
def start_telegram():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    executor.start_polling(dp, skip_updates=True)
