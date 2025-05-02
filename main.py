from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import random

app = FastAPI()

# CORS برای مینی‌اپ تلگرام و سیستم پرداخت
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در نسخه نهایی به دامنه‌های خودت محدودش کن
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# لیست لینک‌های سیستم پرداخت (10 سرور روی Vercel)
PAYMENT_SERVERS = [
    "https://payment-1.vercel.app/api/transaction",
    "https://payment-2.vercel.app/api/transaction",
    "https://payment-3.vercel.app/api/transaction",
    # ...
    "https://payment-10.vercel.app/api/transaction"
]

# کاربران متصل شده
connected_users = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = websocket.query_params.get("userId")

    if user_id:
        connected_users[user_id] = websocket
        try:
            while True:
                message = await websocket.receive_json()
                if message.get("type") == "payment_request":
                    await handle_payment_request(user_id, message)
        except WebSocketDisconnect:
            connected_users.pop(user_id, None)

# هندل‌کردن درخواست پرداخت و ارسال به یکی از سرورهای پرداخت
async def handle_payment_request(user_id, message):
    payment_data = message.get("data")
    selected_url = random.choice(PAYMENT_SERVERS)

    try:
        response = requests.post(selected_url, json=payment_data)
        response_data = response.json()
        # ارسال پاسخ به کلاینت از طریق وب‌سوکت
        if user_id in connected_users:
            await connected_users[user_id].send_json({
                "event": "payment_response",
                "data": response_data
            })
    except Exception as e:
        print(f"Payment request failed: {e}")
        if user_id in connected_users:
            await connected_users[user_id].send_json({
                "event": "payment_error",
                "data": {"error": str(e)}
            })

# ارسال نوتیفیکیشن به کاربر خاص
@app.post("/notify")
async def notify_user(payload: dict):
    user_id = payload.get("userId")
    event = payload.get("event")
    data = payload.get("data", {})

    if user_id in connected_users:
        await connected_users[user_id].send_json({
            "event": event,
            "data": data
        })
        return {"status": "sent"}
    return {"status": "user_not_connected"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
