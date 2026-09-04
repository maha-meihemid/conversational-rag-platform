import time
from collections import defaultdict, deque
from collections.abc import Callable
from math import ceil
from threading import Lock


class RateLimiter:
    def __init__(
        self,
        requests: int,
        window_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self._clock = clock
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, client_id: str) -> int | None:
        now = self._clock()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = self._requests[client_id]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= self.requests:
                return max(1, ceil(timestamps[0] + self.window_seconds - now))

            timestamps.append(now)
            return None
