import asyncio
import html
import os
import threading
import time
import urllib.request

from flask import Flask
from telethon import TelegramClient, events, utils
from telethon.sessions import StringSession
from telethon.tl.custom import Button


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"المتغير البيئي {name} غير موجود في إعدادات Render")
    return value


api_id_raw = required_env("API_ID")
try:
    api_id = int(api_id_raw)
except ValueError as exc:
    raise RuntimeError("API_ID يجب أن يكون رقمًا صحيحًا") from exc

api_hash = required_env("API_HASH")
session_string = required_env("SESSION_STRING")
ALERT_TARGET = required_env("ALERT_TARGET")

KEEP_ALIVE_INTERVAL = max(60, int(os.environ.get("KEEP_ALIVE_INTERVAL", "300")))
KEEP_ALIVE_URL = (
    os.environ.get("KEEP_ALIVE_URL", "").strip()
    or os.environ.get("RENDER_EXTERNAL_URL", "").strip()
).rstrip("/")


KEYWORDS = ["يساعدني", "يحل", "يحِل", "يسوي"]
EXCLUDED = [
    "بأسعار", "بسعر", "باسعار", "للتواصل", "مشكلتها", "مشكلتي", "تخصص",
    "التخصص", "مشكلة", "المشكله", "تواصل واتس", "التواصل", "للحجز",
    "خصم خاص", "عرض خاص", "تدفعون لهم بعد", "الدفع بعد", "نقدم لك",
    "نقدم لكم", "خدماتنا", "خدمة تعليمية", "تواصل الآن", "تواصل معنا",
    "تواصلوا معنا", "يحلف", "إذا تبون", "مايسوي", "ذي تسوي", "ذا يسوي",
    "ذي يسوي", "انا اسوي", "يبي", "اعرف حد", "اعرف واحد", "الموزونات",
    "المنصة", "الموازونة", "انقبل", "التحويل", "رغبات", "الرغبات", "قبول",
    "القبول", "يسوي له", "هذا يحل", "اسوي له", "يحتاج إلى حد", "يحتاج حد",
    "اعرف شخص", "القيد", "قيد", "منصه", "اذا تبون", "يحليلك", "موراضي",
    "يحلوين", "يحلليلك", "نقدم", "أقدم", "اقدم", "شسوي", "ما يسوي",
    "مشكله", "الدعم", "المنصه", "الاستيب", "الستيب", "ستيب", "للقبول",
    "بالقبول", "تبي", "الذي حابب",
]

TARGET_CHAT_ID = 4415468101
TARGET_CHAT_ID_FULL = -1004415468101
TARGET_CHAT_USERNAME = ALERT_TARGET.lstrip("@").lower()

client = TelegramClient(StringSession(session_string), api_id, api_hash)


def contains_keyword(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    if any(keyword.lower() in lowered for keyword in KEYWORDS):
        return True
    extra_phrases = [
        "ابغى حد", "أبغى حد", "ابغى احد", "أبغى احد", "ابغى خصوصي",
        "أبغى خصوصي", "ابغى شخص", "أبغى شخص", "ابغى واحد", "أبغى واحد",
        "احد يساعد", "أحد يساعد", "من يساعد", "حد يساعد", "شخص يساعد",
    ]
    return any(phrase in lowered for phrase in extra_phrases)


def build_chat_link(chat, chat_id, message_id):
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{message_id}"
    value = str(chat_id)
    if value.startswith("-100"):
        return f"https://t.me/c/{value[4:]}/{message_id}"
    return None


@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if event.chat_id in (TARGET_CHAT_ID, TARGET_CHAT_ID_FULL):
        return
    try:
        text = event.message.message or ""
        if not text or not contains_keyword(text) or any(word in text for word in EXCLUDED):
            return

        chat = await event.get_chat()
        chat_username = getattr(chat, "username", None)
        if chat_username and chat_username.lower() == TARGET_CHAT_USERNAME:
            return

        sender = await event.get_sender()
        sender_name = utils.get_display_name(sender) if sender else "مجهول"
        if sender and getattr(sender, "username", None):
            sender_user_field = f"@{sender.username}"
        elif sender and getattr(sender, "id", None):
            sender_user_field = sender_name
        else:
            sender_user_field = "لا يوجد"

        sender_id = sender.id if sender and getattr(sender, "id", None) else "غير معروف"
        chat_title = getattr(chat, "title", None) or getattr(chat, "first_name", None) or "المجموعة"
        chat_link = build_chat_link(chat, event.chat_id, event.message.id)
        header = (
            "📢 رسالة مهمة:\n\n"
            f"👤 المرسل: {html.escape(sender_name)}\n"
            f"🆔 : tg://openmessage?user_id={sender_id}\n"
            f"🔗 اليوزر: {sender_user_field}\n"
            f"المجموعة: {html.escape(chat_title)}\n"
            f"🔗 رابط الرسالة: {chat_link or 'لا يمكن توليد رابط عام'}\n"
            "— الرسالة محوله 👇 —"
        )

        buttons = [[Button.url("🔗 الانتقال إلى الرسالة", chat_link)]] if chat_link else []
        await client.send_message(ALERT_TARGET, header, buttons=buttons)
        try:
            await client.forward_messages(ALERT_TARGET, event.message)
        except Exception:
            await client.send_message(
                ALERT_TARGET,
                "💬 لم أستطع إعادة توجيه الرسالة، وهذا نصها:\n\n" + text,
            )
    except Exception as exc:
        print("Error handling message:", repr(exc), flush=True)


app = Flask(__name__)


@app.get("/")
def home():
    return "Telegram bot is running", 200


@app.get("/health")
def health():
    return "OK", 200


def keep_alive_loop():
    """إيقاظ داخلي احتياطي؛ لا يعوض المراقب الخارجي إذا أوقفت Render العملية."""
    if not KEEP_ALIVE_URL:
        print("Internal keep-alive disabled: set KEEP_ALIVE_URL or use RENDER_EXTERNAL_URL", flush=True)
        return

    time.sleep(15)
    health_url = f"{KEEP_ALIVE_URL}/health"
    while True:
        try:
            request = urllib.request.Request(
                health_url,
                headers={"User-Agent": "telegram-bot-health-check/1.0"},
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                print(f"Internal keep-alive: HTTP {response.status}", flush=True)
        except Exception as exc:
            print(f"Internal keep-alive error: {exc!r}", flush=True)
        time.sleep(KEEP_ALIVE_INTERVAL)


def run_flask_app():
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)


async def main():
    threading.Thread(target=run_flask_app, name="flask-server", daemon=True).start()
    threading.Thread(target=keep_alive_loop, name="internal-keep-alive", daemon=True).start()
    print("Connecting to Telegram...", flush=True)
    await client.start()
    print("Userbot started — listening...", flush=True)
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user", flush=True)
