# tests/fakes/fake_bp.py
class Seq:
    """按顺序返回 items；item 是 Exception 则抛出。用来模拟“返回序列”。"""
    def __init__(self, items):
        self.items = list(items)
        self.i = 0

    def next(self):
        if self.i >= len(self.items):
            x = self.items[-1]
        else:
            x = self.items[self.i]
            self.i += 1
        if isinstance(x, Exception):
            raise x
        return x


class FakeMarketsDAO:
    def __init__(self, market=None, ticker=None, markets_list=None):
        self._market = market or {"priceIncrement": "0.0001"}
        self._ticker = ticker or {"c": "1.72"}
        self._markets_list = markets_list or [{"symbol": "ASTER_USDC_PERP"}]

    def markets(self):
        return self._markets_list

    def market(self, symbol: str):
        return self._market

    def ticker(self, symbol: str):
        return self._ticker


class FakeOrderDAO:
    def __init__(self, execute_seq=None, get_seq=None, cancel_seq=None):
        self.execute_seq = execute_seq or Seq([[{"orderId": "1", "status": "New"}]])
        self.get_seq = get_seq or Seq([{"status": "FILLED"}])
        self.cancel_seq = cancel_seq or Seq([{"ok": True}])

        self.execute_calls = []
        self.get_calls = []
        self.cancel_calls = []

    def execute(self, **kwargs):
        self.execute_calls.append(kwargs)
        return self.execute_seq.next()

    def get(self, **kwargs):
        self.get_calls.append(kwargs)
        return self.get_seq.next()

    def cancel(self, **kwargs):
        self.cancel_calls.append(kwargs)
        return self.cancel_seq.next()