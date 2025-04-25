from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# اجازه CORS برای مینی‌اپ و سیستم پرداخت
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # بهتره اینو محدود کنی به دامنه خودت در نسخه نهایی
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_users = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = websocket.query_params.get("userId")
    if user_id:
        connected_users[user_id] = websocket
        try:
            while True:
                await websocket.receive_text()  # گوش می‌کنه ولی فعلاً استفاده نمی‌کنیم
        except WebSocketDisconnect:
            del connected_users[user_id]

@app.post("/notify")
async def notify_user(user_id: str, new_balance: float):
    if user_id in connected_users:
        await connected_users[user_id].send_json({
            "userId": user_id,
            "newBalance": new_balance
        })
        return {"status": "sent"}
    return {"status": "user_not_connected"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
