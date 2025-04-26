from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# CORS برای مینی‌اپ تلگرام و سیستم پرداخت
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در نسخه نهایی به دامنه‌های خودت محدودش کن
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                # پیام‌های دریافتی از کلاینت را می‌توان اینجا پردازش کرد
                await websocket.receive_text()
        except WebSocketDisconnect:
            connected_users.pop(user_id, None)

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
