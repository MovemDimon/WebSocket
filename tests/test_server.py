import socketio
import pytest
import time

# آدرس هاست WebSocket که روی Render اجرا میشه
WEBSOCKET_URL = 'https://your-websocket-host.onrender.com'

# فرض بر اینه که WebSocket سرور از query parameter به نام userId استفاده می‌کنه
USER_ID = "test-user-123"

def test_websocket_connection():
    sio = socketio.Client()

    connected = False

    @sio.event
    def connect():
        nonlocal connected
        connected = True
        print("✅ Connected to WebSocket")

    @sio.event
    def connect_error(data):
        print("❌ Connection failed!")

    @sio.event
    def disconnect():
        print("🔌 Disconnected from server")

    # اتصال با userId در query string
    sio.connect(f'{WEBSOCKET_URL}?userId={USER_ID}', transports=['websocket'])

    time.sleep(1)  # کمی صبر برای برقراری اتصال

    sio.disconnect()

    assert connected, "WebSocket connection failed!"
