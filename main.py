import asyncio
import random
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from starlette.websockets import WebSocketState
from app.core.app_core_config import Config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# —————————————————————————————
# لیست ثابت سرورهای پرداخت Vercel
# —————————————————————————————
PAYMENT_SERVERS = [
    "https://vercel-app-10-xxxx.vercel.app/api/transaction",
    "https://vercel-app-50-xxxx.vercel.app/api/transaction",
    "https://vercel-app-70-xxxx.vercel.app/api/transaction",
    "https://vercel-app-110-xxxx.vercel.app/api/transaction",
    "https://vercel-app-120-xxxx.vercel.app/api/transaction",
]
# کلید API از Config
API_KEY = Config.WS_API_KEY
healthy_servers = PAYMENT_SERVERS.copy()
connected_users: Dict[str, WebSocket] = {}

async def health_check():
    async with httpx.AsyncClient(timeout=5) as client:
        while True:
            new_healthy = []
            for url in PAYMENT_SERVERS:
                try:
                    # هر بار مسیر /api/transaction رو به /health تبدیل می‌کنیم
                    health_url = url.replace("/api/transaction", "/health")
                    r = await client.get(
                        health_url,
                        headers={"X-API-KEY": API_KEY}
                    )
                    if r.status_code == 200:
                        new_healthy.append(url)
                except Exception as e:
                    print(f"[health_check] error checking {url}: {e}")
            if new_healthy:
                healthy_servers.clear()
                healthy_servers.extend(new_healthy)
            await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(health_check())

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
            if action in ["confirm_payment", "payment_request"]:
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
