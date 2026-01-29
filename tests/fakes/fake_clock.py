# tests/fakes/fake_clock.py
class FakeClock:
    """
    控制 time.time() / time.sleep()：
    - time() 返回当前秒数
    - sleep(x) 让时间前进 x 秒
    """
    def __init__(self, start=0.0):
        self.t = float(start)

    def time(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += float(seconds)