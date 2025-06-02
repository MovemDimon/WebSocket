import re
import json
import base64
import asyncio
import websockets
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from app.core.app_core_config import Config

CURRENCY, NETWORK, WALLET, TX_HASH = range(4)

WALLET_REGEX = re.compile(r"^(0x[a-fA-F0-9]{40}|EQ[a-zA-Z0-9_-]{48})$")
TX_HASH_REGEX = re.compile(r"^[A-Fa-f0-9]{64}$")

async def send_via_websocket(user_id: str, data: dict) -> dict:
    uri = f"{Config.WS_SERVER_URL}?userId={user_id}&api_key={Config.WS_API_KEY}"
    try:
        async with websockets.connect(
            uri,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        ) as ws:
            await ws.send(json.dumps({"action": "confirm_payment", "data": data}))
            async for message in ws:
                msg = json.loads(message)
                if msg.get("event") == "payment_result":
                    return msg["data"]
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def start_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    args = context.args[0] if context.args else None
    if args and args.startswith("pay_"):
        decoded = json.loads(base64.b64decode(args.split("_", 1)[1]).decode())
        context.user_data["package"] = decoded

    keyboard = [[InlineKeyboardButton("USDT", callback_data="USDT")]]
    await update.message.reply_text(
        "Welcome! Please select the currency for your purchase (only USDT is supported):",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CURRENCY

async def select_network(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["currency"] = update.callback_query.data
    networks = ["Ethereum", "BSC", "Polygon", "Arbitrum", "Optimism", "TON"]
    keyboard = [[InlineKeyboardButton(net, callback_data=net)] for net in networks]
    await update.callback_query.edit_message_text(
        f"Please select the network for {context.user_data['currency']}:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return NETWORK

async def get_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["network"] = update.callback_query.data
    await update.callback_query.edit_message_text(
        "Great! Now please enter your wallet address (the address you will send USDT from):"
    )
    return WALLET

async def ask_tx_hash(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    wallet = update.message.text.strip()
    if not WALLET_REGEX.match(wallet):
        await update.message.reply_text("❌ Invalid wallet address format. Please try again.")
        return WALLET

    context.user_data["wallet"] = wallet
    pkg = context.user_data.get("package", {})
    amount = pkg.get("usdPrice")
    currency = context.user_data["currency"]

    # انتخاب آدرس مقصد بر اساس شبکه
    if context.user_data["network"] == "TON":
        merchant = Config.TON_MERCHANT_WALLET
    else:
        merchant = Config.ETH_MERCHANT_WALLET

    # ذخیره merchant در user_data برای استفاده بعدی
    context.user_data["merchant"] = merchant

    await update.message.reply_text(
        f"Please send exactly {amount} {currency} to the address below:\n\n`{merchant}`\n\n"
        "After payment, please reply with the transaction hash (tx_hash).",
        parse_mode="Markdown"
    )
    return TX_HASH

async def receive_tx_hash(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tx_hash = update.message.text.strip()
    if not TX_HASH_REGEX.match(tx_hash):
        await update.message.reply_text("❌ Invalid transaction hash. Please try again.")
        return TX_HASH

    context.user_data["tx_hash"] = tx_hash
    pkg = context.user_data.get("package", {})
    merchant = context.user_data.get("merchant")  # اینجا از مقدار ذخیره‌شده استفاده می‌کنیم

    data = {
        "user_id": pkg.get("userId"),
        "currency": context.user_data["currency"],
        "network": context.user_data["network"],
        "amount": pkg.get("usdPrice"),
        "merchant_wallet": merchant,
        "sender_wallet": context.user_data["wallet"],
        "tx_hash": tx_hash,
    }

    result = await send_via_websocket(str(data["user_id"]), data)
    if result.get("status") == "confirmed":
        await update.message.reply_text("✅ Your payment has been confirmed! Your purchase is now active.")
    else:
        await update.message.reply_text(f"❌ Payment failed or error: {result.get('message', 'Unknown error')}")

    return ConversationHandler.END

app_builder = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_payment)],
    states={
        CURRENCY: [CallbackQueryHandler(select_network)],
        NETWORK: [CallbackQueryHandler(get_wallet)],
        WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_tx_hash)],
        TX_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_tx_hash)],
    },
    fallbacks=[]
)

app_builder.add_handler(conv_handler)

if __name__ == "__main__":
    app_builder.run_polling()
