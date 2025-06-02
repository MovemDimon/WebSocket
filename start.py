import subprocess
import asyncio

async def main():
    # اجرای سرور FastAPI
    fastapi_proc = subprocess.Popen([
        "gunicorn", "main:app",
        "--worker-class", "eventlet",
        "-w", "1", "-b", "0.0.0.0:8080"
    ])

    # اجرای ربات تلگرام
    bot_proc = subprocess.Popen(["python3", "bot_telegram.py"])

    # منتظر بمون (یا از نظر تمیزتر مدیریت سیگنال‌ها داشته باشی)
    await asyncio.sleep(999999)

asyncio.run(main())
