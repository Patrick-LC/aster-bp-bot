import allure
from decimal import Decimal
from datetime import datetime, timezone

from tests.fakes.fake_bp import FakeMarketsDAO, FakeOrderDAO, Seq
from tests.fakes.fake_aster import FakeTradeDAO


# ------------------------------
# Pure helpers (no external deps)
# ------------------------------

@allure.epic("ASTER-BP Hedge Bot")
@allure.feature("Core helpers")
def test_decimals_from_tick_ok(patch_time):
    m = patch_time
    assert m.decimals_from_tick("0.0001") == 4


@allure.epic("ASTER-BP Hedge Bot")
@allure.feature("Core helpers")
def test_decimals_from_tick_invalid_returns_default(patch_time):
    m = patch_time
    assert m.decimals_from_tick("not-a-number") == 6


@allure.epic("ASTER-BP Hedge Bot")
@allure.feature("Core helpers")
def test_floor_to_increment_round_down(patch_time):
    m = patch_time
    assert m.floor_to_increment(Decimal("1.23456"), Decimal("0.01")) == Decimal("1.23")


# ------------------------------
# Market / price helpers (use simple stubs)
# ------------------------------

@allure.epic("ASTER-BP Hedge Bot")
@allure.feature("Market helpers")
def test_resolve_symbol_prefers_perp_when_requested(patch_time):
    m = patch_time

    class StubMarkets:
        def markets(self):
            return [
                {"symbol": "ASTER_USDC"},
                {"symbol": "ASTER_USDC_PERP"},
            ]

    got = m.resolve_symbol(StubMarkets(), requested_symbol="BAD", base_hint="ASTER", want_perp=True)
    assert "PERP" in got


@allure.epic("ASTER-BP Hedge Bot")
@allure.feature("Market helpers")
def test_get_bp_price_increment_and_decimals_from_market_dict(patch_time):
    m = patch_time

    class StubMarkets:
        def market(self, symbol: str):
            return {"priceIncrement": "0.0001"}

    inc, dec = m.get_bp_price_increment_and_decimals(StubMarkets(), "ASTER_USDC_PERP")
    assert str(inc) == "0.0001"
    assert dec == 4


@allure.epic("ASTER-BP Hedge Bot")
@allure.feature("Market helpers")
def test_get_bp_last_price_reads_c_field(patch_time):
    m = patch_time

    class StubMarkets:
        def ticker(self, symbol: str):
            return {"c": "1.72"}

    px = m.get_bp_last_price(StubMarkets(), "ASTER_USDC_PERP")
    assert px == Decimal("1.72")


# ------------------------------
# Order status helper (use stub that raises)
# ------------------------------

@allure.epic("ASTER-BP Hedge Bot")
@allure.feature("BP order status")
def test_check_bp_order_status_filled(patch_time):
    m = patch_time

    class StubOrders:
        def get(self, orderId: str, symbol: str):
            return {"status": "FILLED"}

    ok, info = m.check_bp_order_status_alternative(StubOrders(), "1", "ASTER_USDC_PERP")
    assert ok is True
    assert info == "FILLED"


@allure.epic("ASTER-BP Hedge Bot")
@allure.feature("BP order status")
def test_check_bp_order_status_404_returns_none(patch_time):
    m = patch_time

    class StubOrders:
        def get(self, orderId: str, symbol: str):
            raise RuntimeError("HTTP 404 RESOURCE_NOT_FOUND")

    ok, info = m.check_bp_order_status_alternative(StubOrders(), "1", "ASTER_USDC_PERP")
    assert ok is None
    assert info == "NOT_FOUND_MAYBE_FILLED"


# ------------------------------
# Funding time logic
# ------------------------------

@allure.epic("ASTER-BP Hedge Bot")
@allure.feature("Funding time")
def test_should_stop_for_funding_true(monkeypatch, m):
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # 07:56 UTC -> next funding 08:00 UTC, remaining 4 minutes
            return datetime(2026, 1, 1, 7, 56, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(m, "datetime", FakeDatetime)
    stop, reason = m.should_stop_for_funding(stop_before_minutes=5)
    assert stop is True
    assert "还有" in reason


# ------------------------------
# Core cycle tests (use your fakes)
# ------------------------------

@allure.epic("ASTER-BP Hedge Bot")
@allure.feature("Hedge cycle")
@allure.story("Leg1 relist then filled, hedge BUY succeeds")
def test_execute_cycle_leg1_relist_then_fill(monkeypatch, patch_time):
    m = patch_time

    # 用“快进时间”的方式保证触发 elapsed==10 的取消+重挂分支。
    # IMPORTANT: 这里只改模块内 m.time（fake time object），不动 stdlib time。
    t = {"sec": 0.0}

    def fake_time():
        return t["sec"]

    def fast_sleep(_):
        t["sec"] += 10

    monkeypatch.setattr(m.time, "time", fake_time)
    monkeypatch.setattr(m.time, "sleep", fast_sleep)

    bp_markets = FakeMarketsDAO(
        ticker={"c": "1.72"},
        market={"priceIncrement": "0.0001"},
    )

    bp_orders = FakeOrderDAO(
        execute_seq=Seq([
            [{"orderId": "1", "status": "New"}],
            [{"orderId": "2", "status": "New"}],
            [{"orderId": "3", "status": "New"}],
        ]),
        get_seq=Seq([
            {"status": "New", "filledQuantity": "0", "quantity": "10"},  # elapsed=0
            {"status": "New", "filledQuantity": "0", "quantity": "10"},  # elapsed=10 -> 触发重挂
            {"status": "FILLED", "filledQuantity": "10", "quantity": "10"},
            {"status": "FILLED", "filledQuantity": "10", "quantity": "10"},
        ]),
        cancel_seq=Seq([{"ok": True}] * 10),
    )

    aster_trade = FakeTradeDAO()

    m.execute_hedge_cycle(
        bp_markets, bp_orders, aster_trade,
        bp_symbol="ASTER_USDC_PERP",
        aster_symbol="ASTERUSDT",
        quantity="10",
        offset_percent=Decimal("0.002"),
        price_increment=Decimal("0.0001"),
        price_decimals=4,
        first_wait_seconds=10,
        recv_window=5000,
        cycle_count=1,
        trade_cfg={"between_legs_sleep": 0},
    )

    # 断言：发生过 cancel（说明 10 秒重挂触发）
    assert len(bp_orders.cancel_calls) >= 1

    # 断言：Aster 两腿都有对冲（BUY/SELL）
    sides = [c.get("side") for c in aster_trade.place_calls]
    assert "BUY" in sides and "SELL" in sides


@allure.epic("ASTER-BP Hedge Bot")
@allure.feature("Hedge cycle")
@allure.story("Leg1 hedge fails but leg2 still runs")
def test_execute_cycle_aster_fail_still_runs_leg2(patch_time):
    m = patch_time

    bp_markets = FakeMarketsDAO(
        ticker={"c": "1.72"},
        market={"priceIncrement": "0.0001"},
    )

    # 两腿 BP 都直接成交
    bp_orders = FakeOrderDAO(
        execute_seq=Seq([
            [{"orderId": "1", "status": "New"}],
            [{"orderId": "2", "status": "New"}],
        ]),
        get_seq=Seq([
            {"status": "FILLED", "filledQuantity": "10", "quantity": "10"},
            {"status": "FILLED", "filledQuantity": "10", "quantity": "10"},
        ]),
    )

    # 自定义一个 trade stub：第 1 次 place_order 抛错（BUY 失败），第 2 次成功（SELL 成功）
    class TradeStub:
        def __init__(self):
            self.place_calls = []
            self._n = 0

        def place_order(self, symbol, side, order_type, quantity, recv_window):
            self.place_calls.append({
                "symbol": symbol,
                "side": side,
                "order_type": order_type,
                "quantity": quantity,
                "recv_window": recv_window,
            })
            self._n += 1
            if self._n == 1:
                raise RuntimeError("aster down")
            return {"orderId": 200, "status": "FILLED"}

        def get_order(self, symbol, order_id: int):
            return {"status": "FILLED", "executedQty": "10", "origQty": "10"}

    aster_trade = TradeStub()

    m.execute_hedge_cycle(
        bp_markets, bp_orders, aster_trade,
        bp_symbol="ASTER_USDC_PERP",
        aster_symbol="ASTERUSDT",
        quantity="10",
        offset_percent=Decimal("0.002"),
        price_increment=Decimal("0.0001"),
        price_decimals=4,
        first_wait_seconds=10,
        recv_window=5000,
        cycle_count=1,
        trade_cfg={"between_legs_sleep": 0},
    )

    # BP 两腿都有下单
    assert len(bp_orders.execute_calls) == 2

    # Aster 两腿都有尝试（BUY + SELL）
    sides = [c.get("side") for c in aster_trade.place_calls]
    assert "BUY" in sides and "SELL" in sides