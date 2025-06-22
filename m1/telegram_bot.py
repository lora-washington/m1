import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from utils.pnl_logger import read_latest_pnl
from websocket.bybit_ws_client import BybitWebSocketClient
from bots.momentum_ws_bot import MomentumBot
from bots.grid_ws_bot import GridBot
import json

with open("config.json") as f:
    config = json.load(f)

API_KEY = config["API_KEY"]
API_SECRET = config["API_SECRET"]
PAIRS = config["PAIRS"]


from config import momentum as momentum_config
from config import grid as grid_config

API_TOKEN = "7433663009:AAEEUjVHMDRLcn9a95YYCWVnmNOxed8YLl4"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

running_bots = []

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer("\u2705 Бот запущен. Запускаю торговлю...")

    for symbol in PAIRS:
        m_bot = MomentumBot(
            api_key=API_KEY,
            api_secret=API_SECRET,
            symbol=symbol,
            **momentum_config
        )
        g_bot = GridBot(
            api_key=API_KEY,
            api_secret=API_SECRET,
            symbol=symbol,
            **grid_config
        )

        task_m = asyncio.create_task(m_bot.start())
        task_g = asyncio.create_task(g_bot.start())

        running_bots.append((task_m, m_bot))
        running_bots.append((task_g, g_bot))

@dp.message_handler(commands=["stop"])
async def stop_handler(message: types.Message):
    for task, bot_instance in running_bots:
        task.cancel()
    running_bots.clear()
    await message.answer("\ud83d\udd1a Бот остановлен. Остановить процессы можно через Telegram-управление.")

@dp.message_handler(commands=["status"])
async def status_handler(message: types.Message):
    pnl = read_latest_pnl()
    await message.answer(f"\ud83d\udcca Последние сделки:\n<pre>{pnl}</pre>", parse_mode=ParseMode.HTML)

    balance = await BybitWebSocketClient(API_KEY, API_SECRET, "BTCUSDT").get_balance()
    await message.answer(f"\ud83d\udcb0 Баланс USDT: {balance.get('USDT', 0)}")

