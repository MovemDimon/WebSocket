import os
from dotenv import load_dotenv

# بارگذاری مقادیر از .env
load_dotenv()

class Config:
    # توکن ربات تلگرام
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    # API Key برای WebSocket
    WS_API_KEY: str = os.getenv("WS_API_KEY", "")
    # آدرس والت فروشنده برای پرداخت
    MERCHANT_WALLET_ADDRESS: str = os.getenv("MERCHANT_WALLET_ADDRESS", "")
    # URL کامل WebSocket (بدون کوئری استرینگ)
    WS_SERVER_URL: str = os.getenv("WS_SERVER_URL", "")
