import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from main import app

client = TestClient(app)

def test_ws_rejects_wrong_key():
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws?userId=u1&api_key=wrong"):
            pass

def test_ws_accepts_and_closes():
    with client.websocket_connect("/ws?userId=u1&api_key=testkey"):
        pass

def test_notify_user_not_connected():
    resp = client.post(
        "/notify?api_key=testkey",
        json={
            "userId": "u1",
            "event": "evt",
            "data": {}
        }
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "user_not_connected"
