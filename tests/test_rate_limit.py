from app.core.rate_limit import RateLimiter


def test_rate_limiter_blocks_requests_over_limit() -> None:
    now = 100.0
    limiter = RateLimiter(requests=2, window_seconds=60, clock=lambda: now)

    assert limiter.check("client") is None
    assert limiter.check("client") is None
    assert limiter.check("client") == 60


def test_rate_limiter_tracks_clients_separately() -> None:
    limiter = RateLimiter(requests=1, window_seconds=60, clock=lambda: 100.0)

    assert limiter.check("first") is None
    assert limiter.check("second") is None


def test_rate_limiter_allows_requests_after_window() -> None:
    current_time = [100.0]
    limiter = RateLimiter(
        requests=1,
        window_seconds=60,
        clock=lambda: current_time[0],
    )

    assert limiter.check("client") is None
    current_time[0] = 160.0
    assert limiter.check("client") is None
