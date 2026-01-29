# tests/fakes/fake_aster.py
from tests.fakes.fake_bp import Seq


class FakeTradeDAO:
    def __init__(self, place_seq=None, get_order_seq=None):
        # place_order 的返回序列（可含 Exception）
        self.place_seq = place_seq or Seq([{"orderId": 100, "status": "FILLED"}])
        # get_order 的返回序列
        self.get_order_seq = get_order_seq or Seq([
            {"status": "FILLED", "executedQty": "10", "origQty": "10"}
        ])

        self.place_calls = []
        self.get_order_calls = []

    def place_order(self, **kwargs):
        self.place_calls.append(kwargs)
        return self.place_seq.next()

    def get_order(self, **kwargs):
        self.get_order_calls.append(kwargs)
        return self.get_order_seq.next()