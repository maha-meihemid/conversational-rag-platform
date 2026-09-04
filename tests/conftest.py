from pathlib import Path

import pytest

API_TEST_FILES = {
    "test_assistant_profile.py",
    "test_chat_api.py",
    "test_health.py",
    "test_logging.py",
    "test_metrics.py",
    "test_web_app.py",
}
INTEGRATION_TEST_FILES = {"test_conversation.py"}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        filename = Path(str(item.path)).name
        if filename in API_TEST_FILES:
            item.add_marker(pytest.mark.api)
        elif filename in INTEGRATION_TEST_FILES:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
