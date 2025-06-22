import asyncio
import websockets
import json
import hmac
import hashlib
import time
import requests
import aiohttp

class BybitWebSocketClient:
    def __init__(self, api_key, api_secret, symbol, is_testnet=False, market_type="spot"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol.upper()
        self.market_type = market_type

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

    async def get_balance(self):
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        param_str = "accountType=UNIFIED"

        sign_payload = f"{timestamp}{self.api_key}{recv_window}{param_str}"
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            sign_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        url = f"{self.base_rest_url}/v5/account/wallet-balance?{param_str}"
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "X-BAPI-SIGN": signature,
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                try:
                    result = await response.json()
                except Exception as e:
                    print(f"[ERROR] JSON decode error: {e}")
                    return {"USDT": 0.0}

                if not result or 'result' not in result or not result['result'].get('list'):
                    print("[ERROR] Invalid or empty balance response.")
                    return {"USDT": 0.0}

                coins = result['result']['list'][0]['coin']
                for c in coins:
                    if c['coin'] == 'USDT':
                        return {"USDT": float(c['walletBalance'])}
                return {"USDT": 0.0}

    async def connect(self, callback):
        self.callback = callback
        print(f"[WS CONNECT] Connecting to {self.base_ws_url}")
        async with websockets.connect(self.base_ws_url) as websocket:
            await self.subscribe_price_stream(websocket)
            async for message in websocket:
                await self.handle_message(json.loads(message))

    async def subscribe_price_stream(self, ws):
        msg = {
            "op": "subscribe",
            "args": [f"tickers.{self.symbol}"]
        }
        print(f"[WS SUBSCRIBE] {msg}")
        await ws.send(json.dumps(msg))

    async def handle_message(self, msg):
        if "data" not in msg:
            return
        price = msg["data"].get("lastPrice")
        if price:
            print(f"[PRICE STREAM] {self.symbol} → {price}")
            await self.callback(float(price))


    def place_market_order(self, side, qty):
        url = f"{self.base_rest_url}/v5/order/create"
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
    
        body = {
            "category": "spot",
            "symbol": self.symbol,
            "side": side.upper(),
            "orderType": "Market",
            "qty": str(qty),
            "timeInForce": "IOC"
        }
    
        payload = json.dumps(body)
        sign_raw = f"{timestamp}{self.api_key}{recv_window}{payload}"
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            sign_raw.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
    
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "Content-Type": "application/json"
        }
    
        try:
            response = requests.post(url, headers=headers, data=payload)
            result = response.json()
        except Exception as e:
            print(f"[ORDER ERROR] Exception: {e}")
            return None
    
        if result.get("retCode") != 0:
            print(f"[ORDER ERROR] Failed to place order: {result.get('retMsg')}")
            return None
    
        # Успешный ордер
        print(f"[ORDER SUCCESS] {side} {qty} {self.symbol} → OrderID: {result['result'].get('orderId')}")
        return result


# ✅ Пример ручного теста
if __name__ == "__main__":
    api_key = "YOUR_API_KEY"
    api_secret = "YOUR_API_SECRET"
    symbol = "TRXUSDT"
    qty = 50

    client = BybitWebSocketClient(api_key, api_secret, symbol)
    result = client.place_market_order("BUY", qty)
    print(result)

