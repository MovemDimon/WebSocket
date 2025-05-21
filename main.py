import asyncio
import random
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from starlette.websockets import WebSocketState

app = FastAPI()

# CORS settings - اجازه‌ همه‌دامنه‌ها برای توسعه (در پروداکشن محدودتر کنید)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# لیست سرورهای پرداخت و وضعیت سلامت آن‌ها
PAYMENT_SERVERS = [
    "https://payment-1.vercel.app/api/transaction",
    # … تا ۱۰ سرور
    "https://payment-10.vercel.app/api/transaction",
]
healthy_servers = PAYMENT_SERVERS.copy()
API_KEY = "<YOUR_WS_API_KEY>"

async def health_check():
    async with httpx.AsyncClient(timeout=5) as client:
        while True:
            new_healthy = []
            for url in PAYMENT_SERVERS:
                try:
                    r = await client.get(
                        url.replace("/api/transaction", "/health"),
                        headers={"X-API-KEY": API_KEY}
                    )
                    if r.status_code == 200:
                        new_healthy.append(url)
                except Exception as e:
                    # لاگ خطا برای اشکال‌زدایی
                    print(f"[health_check] error checking {url}: {e}")
            if new_healthy:
                healthy_servers.clear()
                healthy_servers.extend(new_healthy)
            await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(health_check())

# نگهداری WebSocket‌های فعال
connected_users: Dict[str, WebSocket] = {}

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., alias="userId"),
    api_key: str = Query(..., alias="api_key")
):
    if api_key != API_KEY:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    connected_users[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action") or data.get("type")
            if action == "confirm_payment" or action == "payment_request":
                # اجرای ناهمزمان درخواست پرداخت
                asyncio.create_task(handle_payment_request(user_id, data.get("data", {})))
    except WebSocketDisconnect:
        connected_users.pop(user_id, None)

async def handle_payment_request(user_id: str, data: dict):
    if not healthy_servers:
        return
    selected_url = random.choice(healthy_servers)
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(
                selected_url,
                json=data,
                headers={"X-API-KEY": API_KEY}
            )
            result = resp.json()
        except Exception as e:
            result = {"status": "error", "message": str(e)}

    ws = connected_users.get(user_id)
    if ws and ws.application_state == WebSocketState.CONNECTED:
        await ws.send_json({"event": "payment_result", "data": result})

@app.post("/notify")
async def notify_user(
    payload: dict,
    api_key: str = Query(..., alias="api_key")
):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    user_id = payload.get("userId") or payload.get("user_id")
    event = payload.get("event")
    data = payload.get("data", {})
    ws = connected_users.get(str(user_id))
    if ws and ws.application_state == WebSocketState.CONNECTED:
        await ws.send_json({"event": event, "data": data})
        return {"status": "sent"}
    return {"status": "user_not_connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
