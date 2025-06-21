from utils.exchange import BybitWebSocketClient  # Убедись, что путь правильный

def init_exchange(api_key, api_secret, symbol="USDT", is_testnet=False):
    print(f"✅ Биржа инициализирована для пары: {symbol}")
    return BybitWebSocketClient(
        api_key=api_key,
        api_secret=api_secret,
        symbol=symbol,
        is_testnet=is_testnet,
        market_type="spot"
    )