import os
from datetime import datetime

LOG_PATH = "logs/pnl_log.txt"

def log_trade(symbol, side, amount, entry_price, exit_price):
    try:
        side = side.upper()
        amount = float(amount)
        entry_price = float(entry_price)
        exit_price = float(exit_price)

        # PnL: реальная прибыль
        pnl = (exit_price - entry_price) * amount if side == "SELL" else (entry_price - exit_price) * amount
        pnl = round(pnl, 4)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        record = f"[{now}] {symbol} | {side} | QTY: {amount:.6f} | IN: {entry_price:.4f} | OUT: {exit_price:.4f} | PnL: {pnl}\n"

        os.makedirs("logs", exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(record)

    except Exception as e:
        print(f"[PNL LOGGER ERROR] Ошибка при логировании: {e}")


def read_latest_pnl():
    if not os.path.exists(LOG_PATH):
        return "No trades yet."
    try:
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()
        return "".join(lines[-10:]) or "No trades yet."
    except Exception as e:
        return f"[READ PNL ERROR] {e}"
