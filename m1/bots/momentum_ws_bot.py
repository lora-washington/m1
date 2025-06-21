import asyncio
import json
from utils.indicators import calculate_rsi, calculate_ema, calculate_obv, calculate_volume_ma, calculate_order_book_pressure
from websocket.bybit_ws_client import BybitWebSocketClient
from utils.pnl_logger import log_trade


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
        self.volumes = []
        self.order_books = []
        self.in_position = False
        self.entry_price = None
        self.amount = None
        self.high_price = None
        self.trailing_stop = None

    async def start(self):
        await self.client.connect(self.on_price_update)

    async def on_price_update(self, price, volume=None, order_book=None):
        price = float(price)
        self.prices.append(price)
        self.volumes.append(float(volume) if volume else 0)
        if order_book:
            self.order_books.append(order_book)

        if len(self.prices) > 100:
            self.prices.pop(0)
            self.volumes.pop(0)
            if self.order_books:
                self.order_books.pop(0)

        if not self.in_position and self.check_entry_signal():
            await self.enter_position(price)
        elif self.in_position:
            await self.manage_position(price)

    def check_entry_signal(self):
        closes = self.prices[-30:]
        volumes = self.volumes[-30:]
        rsi = calculate_rsi(closes, period=14)[-1]
        ema_fast = calculate_ema(closes, period=12)[-1]
        ema_slow = calculate_ema(closes, period=26)[-1]
        obv = calculate_obv(closes, volumes)[-1]
        vol_ma = calculate_volume_ma(volumes, period=14)[-1]
        pressure = calculate_order_book_pressure(self.order_books[-1]) if self.order_books else 0

        return (
            rsi < self.rsi_max and
            ema_fast > ema_slow and
            volumes[-1] > 1.5 * vol_ma and
            pressure > 0.6
        )

    async def enter_position(self, price):
        self.entry_price = price
        self.amount = round(self.capital_per_trade / price, 4)
        self.high_price = price
        self.trailing_stop = price * (1 - self.trailing_stop_pct / 100)
        self.in_position = True

        print(f"[MomentumBot] ENTRY @ {price} x {self.amount}")
        self.client.place_market_order("BUY", self.amount)

    async def manage_position(self, price):
        if price > self.high_price:
            self.high_price = price
            self.trailing_stop = price * (1 - self.trailing_stop_pct / 100)

        if price >= self.entry_price * (1 + self.take_profit_pct / 100):
            print(f"[MomentumBot] TAKE PROFIT @ {price}")
            log_trade(self.symbol, "SELL", self.amount, self.entry_price, price)
            await self.exit_position(price)
        elif price <= self.trailing_stop:
            print(f"[MomentumBot] TRAILING STOP @ {price}")
            log_trade(self.symbol, "SELL", self.amount, self.entry_price, price)
            await self.exit_position(price)

    async def exit_position(self, price):
        print(f"[MomentumBot] EXIT @ {price} → Market sell {self.amount}")
        self.client.place_market_order("SELL", self.amount)
        self.in_position = False
        self.entry_price = None
        self.amount = None
        self.high_price = None
        self.trailing_stop = None
