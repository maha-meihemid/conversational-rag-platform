from app.services.readiness import run_readiness_checks


def passing_check() -> None:
    return None


def failing_check() -> None:
    raise RuntimeError("Private dependency error")


def test_readiness_checks_hide_internal_errors() -> None:
    results = run_readiness_checks(
        {"available": passing_check, "broken": failing_check}
    )

    assert results == {"available": "ok", "broken": "unavailable"}
