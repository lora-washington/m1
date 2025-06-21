import asyncio
import websockets
import json
import hmac
import hashlib
import time
import requests


class BybitWebSocketClient:
    def __init__(self, api_key, api_secret, symbol="DOGEUSDT", is_testnet=False, market_type="spot"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol.upper()
        self.market_type = market_type

        # Актуальные WebSocket URL от Bybit v5
        if market_type == "spot":
            self.base_ws_url = "wss://stream.bybit.com/v5/public/spot"
        elif market_type == "linear":
            self.base_ws_url = "wss://stream.bybit.com/v5/public/linear"
        elif market_type == "inverse":
            self.base_ws_url = "wss://stream.bybit.com/v5/public/inverse"
        else:
            raise ValueError("Unsupported market_type. Use 'spot', 'linear', or 'inverse'.")

        self.base_rest_url = "https://api.bybit.com"
        if is_testnet:
            self.base_rest_url = "https://api-testnet.bybit.com"



    async def connect(self, callback): 
        self.callback = callback
        async with websockets.connect(self.base_ws_url) as websocket:
            await self.subscribe_price_stream(websocket)
            async for message in websocket:
                await self.handle_message(json.loads(message))

    async def subscribe_price_stream(self, ws):
        msg = {
            "topic": f"tickers.{self.symbol.lower()}",
            "event": "sub",
            "params": {}
        }
        await ws.send(json.dumps(msg))

    async def handle_message(self, msg):
        if "data" not in msg:
            return
        price = msg["data"].get("lastPrice")
        if price:
            print(f"[PRICE STREAM] {self.symbol} → {price}")

    def place_market_order(self, side, qty):
        url = f"{self.base_rest_url}/spot/v3/order"
        recv_window = 5000
        timestamp = int(time.time() * 1000)

        params = {
            "apiKey": self.api_key,
            "symbol": self.symbol,
            "side": side,
            "type": "MARKET",
            "qty": str(qty),
            "timestamp": timestamp,
            "recvWindow": recv_window
        }

        sign = self._generate_signature(params)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params["sign"] = sign
        response = requests.post(url, headers=headers, data=params)

        try:
            result = response.json()
        except Exception:
            result = response.text

        print(f"[ORDER] {side} {qty} {self.symbol} → {result}")
        return result

    def _generate_signature(self, params):
        sorted_params = sorted(params.items())
        query = "&".join(f"{k}={v}" for k, v in sorted_params)
        return hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()


if __name__ == "__main__":
    import configparser

    config = configparser.ConfigParser()
    config.read("config.ini")
    api_key = config["bybit"]["api_key"]
    api_secret = config["bybit"]["api_secret"]
    symbol = config["bybit"]["symbol"]

    client = BybitWebSocketClient(api_key, api_secret, symbol=symbol)
    asyncio.run(client.connect())
