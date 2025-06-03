# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# نصب وابستگی‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کل پروژه
COPY . .

# اکسپوز پورت FastAPI
EXPOSE 8080

# پیش‌فرض CMD را نگذارید؛ هر سرویس دستور خود را خواهد داشت
