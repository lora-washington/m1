import os
from datetime import datetime

LOG_PATH = "logs/pnl_log.txt"

def log_trade(symbol, side, amount, entry_price, exit_price):
    pnl = (exit_price - entry_price) * amount if side == "BUY" else (entry_price - exit_price) * amount
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    record = f"[{now}] {symbol} | {side} | QTY: {amount} | IN: {entry_price} | OUT: {exit_price} | PnL: {round(pnl, 4)}\n"

    os.makedirs("logs", exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(record)

def read_latest_pnl():
    if not os.path.exists(LOG_PATH):
        return "No trades yet."
    with open(LOG_PATH, "r") as f:
        lines = f.readlines()
    return "".join(lines[-10:])