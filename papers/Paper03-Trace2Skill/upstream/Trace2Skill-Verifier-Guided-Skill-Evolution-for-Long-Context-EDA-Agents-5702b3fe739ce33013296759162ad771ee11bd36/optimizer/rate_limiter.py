#!/usr/bin/env python3
"""Global rate limiter and request counter for the CVDP prompt optimizer.

Enforces a hard request-per-minute limit across ALL API call paths
(mutation, crossover, analyzer, rollouts) to prevent rate-limit bans.

Also provides a circuit breaker that kills the entire optimizer if
consecutive failures exceed a threshold.
"""

from __future__ import annotations

import threading
import time
from collections import deque


class RateLimiter:
    """Thread-safe sliding-window rate limiter.

    Blocks the calling thread until a request slot is available.
    """

    def __init__(self, max_requests_per_minute: int = 80):
        self.max_rpm = max_requests_per_minute
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()
        self._total_requests = 0
        self._total_errors = 0
        self._consecutive_errors = 0
        self._max_total_requests = 50_000
        self._circuit_breaker_threshold = 20

    def wait(self) -> None:
        """Block until a request slot is available within the rate limit."""
        with self._lock:
            if self._total_requests >= self._max_total_requests:
                raise RuntimeError(
                    f"SAFETY: Global request limit reached ({self._max_total_requests} total requests). "
                    f"Stopping to prevent API abuse."
                )
            if self._consecutive_errors >= self._circuit_breaker_threshold:
                raise RuntimeError(
                    f"SAFETY: Circuit breaker tripped ({self._consecutive_errors} consecutive errors). "
                    f"The API may be down or rate-limiting. Stopping."
                )

            now = time.time()
            window_start = now - 60.0
            while self._timestamps and self._timestamps[0] < window_start:
                self._timestamps.popleft()

            if len(self._timestamps) >= self.max_rpm:
                sleep_until = self._timestamps[0] + 60.0
                sleep_time = sleep_until - now + 0.1
                if sleep_time > 0:
                    print(f"  [rate-limit] Throttling: {len(self._timestamps)} requests in last 60s "
                          f"(limit={self.max_rpm}). Sleeping {sleep_time:.1f}s...")
                    self._lock.release()
                    time.sleep(sleep_time)
                    self._lock.acquire()
                    now = time.time()
                    window_start = now - 60.0
                    while self._timestamps and self._timestamps[0] < window_start:
                        self._timestamps.popleft()

            self._timestamps.append(now)
            self._total_requests += 1

    def record_success(self) -> None:
        with self._lock:
            self._consecutive_errors = 0

    def record_error(self) -> None:
        with self._lock:
            self._total_errors += 1
            self._consecutive_errors += 1

    def stats(self) -> dict:
        with self._lock:
            now = time.time()
            recent = sum(1 for t in self._timestamps if t > now - 60)
            return {
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "consecutive_errors": self._consecutive_errors,
                "requests_last_60s": recent,
                "max_rpm": self.max_rpm,
                "max_total": self._max_total_requests,
            }


_global_limiter: RateLimiter | None = None


def get_rate_limiter(max_rpm: int = 80) -> RateLimiter:
    """Get or create the global rate limiter singleton."""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter(max_requests_per_minute=max_rpm)
    return _global_limiter


def reset_rate_limiter() -> None:
    global _global_limiter
    _global_limiter = None
