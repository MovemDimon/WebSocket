import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app, healthy_servers

@pytest.fixture(autouse=True)
def stub_payment(monkeypatch):
    # ارایه یک payment-server تستی
    healthy_servers.clear()
    healthy_servers.append("http://test/api/transaction")
    # Mock کردن httpx.AsyncClient.post
    async def fake_post(self, url, json=None, headers=None):
        class R: 
          def json(self): return {"status":"confirmed","message":"ok","newBalance":123}
        return R()
    monkeypatch.setattr("httpx.AsyncClient.post", fake_post)
    yield

@pytest.mark.asyncio
async def test_full_flow():
    client = TestClient(app)
    with client.websocket_connect("/ws?userId=u1&api_key=testkey") as ws:
        ws.send_json({"action":"confirm_payment","data":{"userId":"u1","coins":10,"usdPrice":5}})
        msg = ws.receive_json()
        assert msg["event"] == "payment_result"
        assert msg["data"]["status"] == "confirmed"
