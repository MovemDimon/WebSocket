import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از .env
load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    WS_API_KEY: str = os.getenv("WS_API_KEY", "")
    # آدرس والت فروشنده برای شبکه‌های ETH (Ethereum, BSC, Polygon, Arbitrum, Optimism)
    ETH_MERCHANT_WALLET: str = os.getenv("ETH_MERCHANT_WALLET", "")
    # آدرس والت فروشنده مخصوص شبکه TON
    TON_MERCHANT_WALLET: str = os.getenv("TON_MERCHANT_WALLET", "")
    WS_SERVER_URL: str = os.getenv("WS_SERVER_URL", "")
