# === m1/bots/momentum_ws_bot.py ===
import asyncio
from utils.indicators import calculate_rsi, calculate_ema
from websocket.bybit_ws_client import BybitWebSocketClient
from utils.pnl_logger import log_trade
import numpy as np

class MomentumBot:
    def __init__(self, api_key, api_secret, symbol, capital_per_trade=50.0, rsi_max=35,
                 take_profit_pct=2.5, trailing_stop_pct=1.2):
        self.client = BybitWebSocketClient(
            api_key=api_key,
            api_secret=api_secret,
            symbol=symbol,
            is_testnet=False,
            market_type="spot"
        )
        self.symbol = symbol
        self.capital_per_trade = capital_per_trade
        self.rsi_max = rsi_max
        self.take_profit_pct = take_profit_pct
        self.trailing_stop_pct = trailing_stop_pct

        self.prices = []
        self.in_position = False
        self.entry_price = None
        self.amount = None
        self.high_price = None
        self.trailing_stop = None
        self.active = True  # теперь бот можно останавливать

    async def start(self):
        await self.client.connect(self.on_price_update)

    async def on_price_update(self, price, *_):
        if not self.active:
            return

        price = float(price)
        print(f"[MOMENTUM DEBUG] Price: {price}, In Position: {self.in_position}")

        self.prices.append(price)
        if len(self.prices) > 100:
            self.prices.pop(0)

        try:
            if not self.in_position and self.check_entry_signal():
                await self.enter_position(price)
            elif self.in_position:
                await self.manage_position(price)
        except Exception as e:
            print(f"[MOMENTUM ERROR] Ошибка в on_price_update: {e}")

    def check_entry_signal(self):
        if len(self.prices) < 30:
            return False

        closes = self.prices[-30:]

        try:
            rsi_series = calculate_rsi(closes, period=14)
            ema_fast_val = calculate_ema(closes, period=12)
            ema_slow_val = calculate_ema(closes, period=26)

            if rsi_series is None or not isinstance(rsi_series, (list, np.ndarray)):
                return False
            if ema_fast_val is None or ema_slow_val is None:
                return False

            rsi_val = rsi_series[-1]

            return rsi_val < self.rsi_max and ema_fast_val > ema_slow_val

        except Exception as e:
            print(f"[ENTRY CHECK ERROR] {e}")
            return False

    async def enter_position(self, price):
        self.entry_price = price
        self.amount = round(self.capital_per_trade / price, 6)
        self.high_price = price
        self.trailing_stop = price * (1 - self.trailing_stop_pct / 100)
        self.in_position = True

        print(f"[ENTRY] BUY @ {price} x {self.amount}")
        try:
            response = self.client.place_market_order("BUY", self.amount)
            print(f"[ORDER RESPONSE] {response}")
        except Exception as e:
            print(f"[ORDER ERROR] {e}")

    async def manage_position(self, price):
        if price > self.high_price:
            self.high_price = price
            self.trailing_stop = price * (1 - self.trailing_stop_pct / 100)

        if price >= self.entry_price * (1 + self.take_profit_pct / 100):
            print(f"[TP] SELL @ {price}")
            await self.exit_position(price)
        elif price <= self.trailing_stop:
            print(f"[TSL] SELL @ {price}")
            await self.exit_position(price)

    async def exit_position(self, price):
        print(f"[EXIT] SELL @ {price}")
        response = self.client.place_market_order("SELL", self.amount)
        print(f"[DEBUG ORDER RESPONSE] {response}")

        try:
            if isinstance(response, dict) and response.get("retCode") == 0:
                log_trade(self.symbol, "SELL", self.amount, self.entry_price, price)
            else:
                print("[LOG WARNING] Ошибка в API, но лог сохраняем.")
                log_trade(self.symbol, "SELL", self.amount, self.entry_price, price)
        except Exception as e:
            print(f"[LOGGING ERROR] {e}")

        self.in_position = False
        self.entry_price = None
        self.amount = None
        self.high_price = None
        self.trailing_stop = None

