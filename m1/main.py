import asyncio
import json
import os
import sys
from bots.grid_ws_bot import GridBot
from bots.momentum_ws_bot import MomentumBot
from telegram_runner import start_telegram
from utils.exchange import init_exchange

# Убедимся, что sys.path обновлён
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def launch_bots(api_key, api_secret, config):
    tasks = []

    for symbol in config["PAIRS"]:
        print(f"🔄 Запуск ботов для {symbol}")
        try:
            if config.get("USE_GRID", True):
                grid_bot = GridBot(api_key, api_secret, symbol, **config["grid"])
                tasks.append(asyncio.create_task(grid_bot.start()))

            if config.get("USE_MOMENTUM", True):
                momentum_bot = MomentumBot(api_key, api_secret, symbol, **config["momentum"])
                tasks.append(asyncio.create_task(momentum_bot.start()))

        except Exception as e:
            print(f"[INIT ERROR] Ошибка при инициализации ботов для {symbol}: {e}")

    return tasks

async def main():
    print("🚀 Запуск всех ботов и Telegram...")

    try:
        with open("config.json") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[CONFIG ERROR] Не удалось загрузить config.json: {e}")
        return

    api_key = config.get("API_KEY")
    api_secret = config.get("API_SECRET")

    if not api_key or not api_secret:
        print("[ERROR] Укажи API_KEY и API_SECRET в config.json")
        return

    bot_tasks = await launch_bots(api_key, api_secret, config)

    # Telegram бот запускаем отдельно
    try:
        asyncio.create_task(start_telegram())
    except Exception as e:
        print(f"[TELEGRAM ERROR] Ошибка запуска Telegram бота: {e}")

    await asyncio.gather(*bot_tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Принудительное завершение.")
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
