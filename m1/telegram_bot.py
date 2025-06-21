import logging
from aiogram import Bot, Dispatcher, types
from utils.pnl_logger import read_latest_pnl
from utils.exchange_client import client
from aiogram.types import ParseMode
from aiogram.utils import executor
import asyncio

API_TOKEN = '7433663009:AAEEUjVHMDRLcn9a95YYCWVnmNOxed8YLl4'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

bots_registry = {}

@dp.message_handler(commands=['start'])
async def start_bot(message: types.Message):
    await message.answer("✅ Бот запущен (псевдо). Настройка исполнения в коде.")
    # Здесь можно подгрузить и запустить конкретного торгового бота по паре

@dp.message_handler(commands=['stop'])
async def stop_bot(message: types.Message):
    await message.answer("🛑 Бот остановлен (псевдо). Настройка исполнения в коде.")
    # Здесь можно остановить активные экземпляры

# оригинал удалён
@dp.message_handler(commands=['status_debug'])
async def status_debug_bot(message: types.Message):
    await message.answer("📊 Статус: все работает (примерный статус). Можно внедрить информацию о ценах, позициях и PnL.")
    # Вывод статуса по позициям и PnL

@dp.message_handler(commands=['restart'])
async def restart_bot(message: types.Message):
    await message.answer("♻️ Перезапуск...")
    # Тут можно реализовать реальный рестарт всех процессов
   

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

@dp.message_handler(commands=['status'])
async def status_bot(message: types.Message):
    pnl = read_latest_pnl()
    await message.answer(f"📊 Последние сделки:\n<pre>{pnl}</pre>", parse_mode=ParseMode.HTML)
    
    balance = await client.get_balance()
    await message.answer(f"💰 Баланс USDT: {balance.get('USDT', 0)}")
