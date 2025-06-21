import asyncio
import json
from telegram_runner import start_telegram
from utils.exchange import init_exchange
from bots.grid_ws_bot import GridBot
from bots.momentum_ws_bot import MomentumBot
import os
import sys
import threading
sys.path.append(os.path.join(os.path.dirname(__file__), "bots"))
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    print("🚀 Запуск всех ботов и Telegram...")

    # Загружаем конфиг
    with open("config.json") as f:
        config = json.load(f)

    api_key = config["API_KEY"]
    api_secret = config["API_SECRET"]
    pairs = config["PAIRS"]

    tasks = []

    for symbol in pairs:
        grid_bot = GridBot(api_key, api_secret, symbol, **config["grid"])
        momentum_bot = MomentumBot(api_key, api_secret, symbol, **config["momentum"])
        tasks.append(asyncio.create_task(grid_bot.start()))
        tasks.append(asyncio.create_task(momentum_bot.start()))

    # Telegram бот в отдельном потоке
    threading.Thread(target=start_telegram, daemon=True).start()

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
