import asyncio
import logging
from decimal import Decimal
from utils.pnl_logger import log_trade
from websocket.bybit_ws_client import BybitWebSocketClient

class GridBot:
    def __init__(self, api_key, api_secret, symbol, grid_size, spread, capital_per_level):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol
        self.grid_size = grid_size
        self.spread_pct = Decimal(str(spread))
        self.capital_per_level = capital_per_level

        self.max_orders = 5  # Можно сделать параметром позже
        self.orders = []
        self.ws_client = BybitWebSocketClient(
          api_key=self.api_key,
          api_secret=self.api_secret,
          symbol=self.symbol,
          is_testnet=False,
          market_type="spot"
        )
        self.initial_price = None
        self.logger = logging.getLogger(__name__)
        self.quantity = None  # Расчёт будет позже в on_price_update


    async def start(self):
        await self.ws_client.connect(self.on_price_update)


    async def on_price_update(self, price, *_):
        price = Decimal(str(price))
        if not self.initial_price:
            self.initial_price = price
            self.generate_grid(price)
            self.quantity = round(self.capital_per_level / float(price), 4)
        self.trade_logic(price)

    def generate_grid(self, center_price):
        self.orders.clear()
        min_price = center_price * (1 - self.spread_pct)
        max_price = center_price * (1 + self.spread_pct)
        step = (max_price - min_price) / self.grid_size

        self.buy_grid = [min_price + step * i for i in range(self.grid_size // 2)]
        self.sell_grid = [max_price - step * i for i in range(self.grid_size // 2)]
        self.logger.info(f"Generated grid for {self.symbol}:\nBuy: {self.buy_grid}\nSell: {self.sell_grid}")

    def trade_logic(self, current_price):
        if len(self.orders) >= self.max_orders:
            self.logger.info("Max open orders reached, skipping")
            return

        for level in self.buy_grid:
            if current_price <= level:
                self.execute_trade('BUY', level, current_price)
                return

        for level in self.sell_grid:
            if current_price >= level:
                self.execute_trade('SELL', level, current_price)
                return

    def execute_trade(self, side, level_price, market_price):
        self.logger.info(f"Executed {side.upper()} at {market_price} (Grid Level: {level_price})")
        pnl = float(self.quantity * (market_price - level_price)) if side == 'SELL' else float(self.quantity * (level_price - market_price))
        log_trade(self.symbol, side.upper(), float(self.quantity), float(level_price), float(market_price))
        self.orders.append({'side': side, 'price': float(market_price)})
        self.ws_client.place_market_order(side.upper(), self.quantity)
        if len(self.orders) > self.max_orders:
            self.orders.pop(0)
        self.generate_grid(market_price)
