import pytest
import main

@pytest.fixture(autouse=True)
def dummy_keys(monkeypatch):
    # مقادیر تستی
    monkeypatch.setenv("API_KEY", "testkey")
    monkeypatch.setenv("WS_API_KEY", "testkey")
    monkeypatch.setattr(main, "API_KEY", "testkey")
    yield
