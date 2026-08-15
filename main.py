import asyncio
import html
import os
import threading
from typing import List

from flask import Flask
from telethon import Button, TelegramClient, events, utils
from telethon.errors import AuthKeyDuplicatedError
from telethon.sessions import StringSession


# ============================================================
# إعدادات Telegram من Environment Variables
# ============================================================


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"متغير البيئة المطلوب غير موجود: {name}")
    return value


def read_account_config(account_number: int):
    """قراءة بيانات حساب واحد من متغيرات مستقلة."""
    api_id_name = f"API_ID_{account_number}"
    api_hash_name = f"API_HASH_{account_number}"
    session_name = f"SESSION_STRING_{account_number}"

    session_string = os.environ.get(session_name, "").strip()

    # السماح بترك حساب كامل غير مستخدم.
    if not session_string:
        return None

    try:
        api_id = int(required_env(api_id_name))
    except ValueError as exc:
        raise RuntimeError(
            f"قيمة {api_id_name} يجب أن تكون رقمًا صحيحًا"
        ) from exc

    api_hash = required_env(api_hash_name)

    return {
        "number": account_number,
        "api_id": api_id,
        "api_hash": api_hash,
        "session_string": session_string,
    }


# لكل حساب API_ID وAPI_HASH وSESSION_STRING خاصة به.
# يمكن ترك الحساب الثاني أو الثالث فارغًا إذا لم يكن مستخدمًا.
ACCOUNT_CONFIGS = [
    config
    for config in (read_account_config(1), read_account_config(2), read_account_config(3))
    if config is not None
]

if not ACCOUNT_CONFIGS:
    raise RuntimeError(
        "أضف بيانات حساب واحدة على الأقل: API_ID_1 وAPI_HASH_1 وSESSION_STRING_1"
    )

ALERT_TARGET = os.environ.get("ALERT_TARGET", "Shaher8642").strip()
ALERT_TARGET = ALERT_TARGET.lstrip("@")


# ============================================================
# شروط التصفية الأصلية — تم الحفاظ عليها كما هي
# ============================================================

KEYWORDS = ["يساعدني", "يحل", "يحِل", "يسوي"]

# قائمة الكلمات المستبعدة
EXCLUDED = [
    "للتواصل", "تواصل واتس", "التواصل", "للحجز", "خصم خاص", "عرض خاص",
    "تدفعون لهم بعد", "نقدم لك", "نقدم لكم", "خدماتنا", "تواصل الآن",
    "تواصل معنا", "تواصلوا معنا", "إذا تبون", "مايسوي", "ذي تسوي",
    "ذا يسوي", "ذي يسوي", "انا اسوي", "يبي", "اعرف حد", "اعرف واحد",
    "يسوي له", "هذا يحل", "اسوي له", "يحتاج إلى حد", "يحتاج حد",
    "اعرف شخص", "تبي", "اذا تبون", "الذي حابب",
]

# يجب وجود كلمة واحدة على الأقل من هذه القائمة
REQUIRED_WORDS = [
    "واجب", "واجبات", "الواجب", "الواجبات",
    "كويز", "كويزات", "الكويز", "الكويزات", "اختبار", "اختبارات",
    "بحث", "بحوث", "البحث", "أوراق", "بحثية", "ورقة علمية",
    "سيرة ذاتية", "سيره ذاتيه", "سيرة", "السيرة الذاتية", "سي في",
    "سيفي", "cv", "بورتفوليو", "portfolio",
    "نشاط", "أنشطة", "النشاط", "الأنشطة",
    "ملف", "ملفات", "الملف",
    "مشروع", "مشاريع", "المشروع", "المشاريع", "بروجكت", "project",
    "ملخص", "ملخصات", "الملخص", "تلخيص", "يلخص",
    "شرح", "يشرح", "الشرح", "شروحات", "الشروحات", "فيديو",
    "تقرير", "تقارير", "التقرير", "التقارير", "ريبورت",
    "عذر", "أعذار", "العذر", "الأعذار",
    "تعديل", "يعدل", "تعديلات", "التعديل", "التعديلات", "تدقيق",
    "تكليف", "التكليف", "أسايمنت", "اسينمنت", "اسايمنت", "سايمنت",
    "الاسايمنت",
    "عرض", "عروض", "العرض", "العروض", "بوربوينت", "بريزنتايشن",
    "ترجمة", "يترجم",
    "ميد", "الميد", "فاينل", "final",
    "يصمم", "تصميم", "التصميم", "التصاميم", "مصمم",
    "ماجستير", "الماجستير",
    "اقتباس", "اقتباسات", "الاقتباس", "الاقتباسات",
    "وأجب", "الوأجب", "واجبي", "وأجبي",
]


# ============================================================
# إعدادات تجاهل المجموعة المستهدفة
# ============================================================

TARGET_CHAT_ID = 3231100427
TARGET_CHAT_ID_FULL = -1003231100427
TARGET_CHAT_USERNAME = ALERT_TARGET.lower()


# ============================================================
# Flask وHealth Check
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "I am alive!", 200


@app.route("/health")
def health():
    return "OK", 200


def run_flask_app() -> None:
    # Render يمرر PORT تلقائيًا، ولا نستخدم رقمًا ثابتًا.
    port = int(os.environ.get("PORT", "10000"))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# ============================================================
# دوال التصفية والروابط
# ============================================================


def contains_keyword(text: str) -> bool:
    if not text:
        return False

    normalized = text.lower()
    if any(keyword.lower() in normalized for keyword in KEYWORDS):
        return True

    abgha_phrases = [
        "ابغى حد", "أبغى حد", "ابغى احد", "أبغى احد",
        "ابغى خصوصي", "أبغى خصوصي", "ابغى شخص", "أبغى شخص",
        "ابغى واحد", "أبغى واحد",
    ]
    if any(phrase.lower() in normalized for phrase in abgha_phrases):
        return True

    yusaed_phrases = [
        "احد يساعد", "أحد يساعد", "من يساعد", "حد يساعد", "شخص يساعد",
    ]
    return any(phrase.lower() in normalized for phrase in yusaed_phrases)


def contains_required_word(text: str) -> bool:
    if not text:
        return False

    normalized = text.lower()
    return any(word.lower() in normalized for word in REQUIRED_WORDS)


def build_chat_link(chat, chat_id, message_id):
    if getattr(chat, "username", None):
        return f"https://t.me/{chat.username}/{message_id}"

    try:
        chat_id_text = str(chat_id)
        if chat_id_text.startswith("-100"):
            short_id = chat_id_text[4:]
            return f"https://t.me/c/{short_id}/{message_id}"
    except Exception:
        pass

    return None


def is_target_chat(event, chat) -> bool:
    if event.chat_id in (TARGET_CHAT_ID, TARGET_CHAT_ID_FULL):
        return True

    chat_username = getattr(chat, "username", None)
    return bool(
        chat_username
        and chat_username.lower() == TARGET_CHAT_USERNAME
    )


# ============================================================
# Handler مستقل لكل حساب
# ============================================================


def register_handler(client: TelegramClient, session_number: int) -> None:
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        # تجاهل الوجهة فورًا قبل أي معالجة إضافية.
        if event.chat_id in (TARGET_CHAT_ID, TARGET_CHAT_ID_FULL):
            return

        try:
            text = event.message.message or ""

            # الشروط الأصلية الثلاثة:
            # 1. كلمة مفتاحية.
            # 2. لا توجد كلمة مستبعدة.
            # 3. توجد كلمة مطلوبة واحدة على الأقل.
            if not text:
                return
            if not contains_keyword(text):
                return
            if any(word in text for word in EXCLUDED):
                return
            if not contains_required_word(text):
                return

            chat = await event.get_chat()
            if is_target_chat(event, chat):
                return

            sender = await event.get_sender()
            sender_name = utils.get_display_name(sender) if sender else "مجهول"

            if sender and getattr(sender, "username", None):
                sender_user_field = f"@{sender.username}"
            elif sender and getattr(sender, "id", None):
                sender_user_field = f"{sender_name}"
            else:
                sender_user_field = "لا يوجد"

            chat_title = (
                getattr(chat, "title", None)
                or getattr(chat, "first_name", None)
                or "المجموعة"
            )
            chat_id = event.chat_id
            chat_link = build_chat_link(chat, chat_id, event.message.id)
            sender_id = (
                sender.id
                if sender and getattr(sender, "id", None)
                else "غير معروف"
            )

            header = (
                "📢 رسالة مهمة:\n\n"
                f"👤 المرسل: {html.escape(sender_name)}\n"
                f"🆔  : tg://openmessage?user_id={sender_id}\n"
                f"🔗 اليوزر : {html.escape(sender_user_field)}\n"
                f" المجموعة: {html.escape(chat_title)}\n"
                f"🔗 رابط الرسالة: "
                f"{chat_link if chat_link else 'لا يمكن توليد رابط عام'}\n"
                "— الرسالة محوله 👇 —"
            )

            buttons = []
            if chat_link:
                buttons.append([
                    Button.url("🔗 الانتقال إلى الرسالة", chat_link)
                ])

            await client.send_message(
                ALERT_TARGET,
                header,
                buttons=buttons,
            )

            try:
                await client.forward_messages(ALERT_TARGET, event.message)
            except Exception as forward_error:
                print(
                    f"[جلسة {session_number}] تعذر إعادة التوجيه: "
                    f"{forward_error!r}"
                )
                await client.send_message(
                    ALERT_TARGET,
                    "💬 (لم أستطع إعادة توجيه الرسالة — "
                    "أدرج النص أدناه):\n\n" + text,
                )

        except Exception as error:
            # الخطأ داخل Handler لا يوقف الجلسة ولا الجلسات الأخرى.
            print(
                f"[جلسة {session_number}] خطأ في معالجة الرسالة: "
                f"{error!r}"
            )


# إنشاء عميل مستقل لكل جلسة موجودة.
clients: List[tuple[int, TelegramClient]] = []

for account in ACCOUNT_CONFIGS:
    session_number = account["number"]
    telegram_client = TelegramClient(
        StringSession(account["session_string"]),
        account["api_id"],
        account["api_hash"],
    )
    register_handler(telegram_client, session_number)
    clients.append((session_number, telegram_client))


# ============================================================
# تشغيل مستقل وإعادة اتصال
# ============================================================


async def run_single_client(
    session_number: int,
    client: TelegramClient,
) -> None:
    """تشغيل جلسة واحدة دون أن يؤثر فشلها على بقية الجلسات."""
    retry_delay = 15

    while True:
        try:
            print(f"[جلسة {session_number}] محاولة الاتصال بـ Telegram...")
            await client.start()
            print(f"[جلسة {session_number}] Userbot started — listening...")

            # ينتظر انقطاع هذه الجلسة فقط.
            await client.run_until_disconnected()
            print(f"[جلسة {session_number}] انقطع الاتصال")

        except AuthKeyDuplicatedError as error:
            # تحتاج هذه الجلسة إلى SESSION_STRING جديدة فقط.
            print(
                f"[جلسة {session_number}] فشل نهائي بسبب "
                f"AuthKeyDuplicatedError: {error!r}. "
                f"غيّر SESSION_STRING_{session_number}."
            )
            return

        except Exception as error:
            # خطأ مؤقت في هذه الجلسة؛ البقية تواصل عملها.
            print(
                f"[جلسة {session_number}] خطأ مستقل: {error!r}. "
                f"ستتم إعادة المحاولة بعد {retry_delay} ثانية."
            )

        finally:
            try:
                if client.is_connected():
                    await client.disconnect()
            except Exception as disconnect_error:
                print(
                    f"[جلسة {session_number}] تعذر إغلاق الاتصال القديم: "
                    f"{disconnect_error!r}"
                )

        await asyncio.sleep(retry_delay)


async def main() -> None:
    flask_thread = threading.Thread(
        target=run_flask_app,
        name="flask-health-server",
        daemon=True,
    )
    flask_thread.start()

    print(
        f"سيتم تشغيل {len(clients)} جلسة Telegram بشكل مستقل..."
    )

    # كل جلسة تعمل في Task مستقلة. استثناء جلسة واحدة لا يلغي الأخرى.
    tasks = [
        asyncio.create_task(
            run_single_client(session_number, client)
        )
        for session_number, client in clients
    ]

    # هذه المهام تعود فقط عند انتهاء AuthKeyDuplicatedError أو إلغاء الخدمة.
    # return_exceptions=True يمنع تسرب استثناء جلسة إلى الجلسات الأخرى.
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for (session_number, _), result in zip(clients, results):
        if isinstance(result, Exception):
            print(
                f"[جلسة {session_number}] انتهت باستثناء: {result!r}"
            )

    # إبقاء Flask حيًا حتى لو توقفت كل جلسات Telegram.
    # هذا يحافظ على /health ويمنع Render من اعتبار الخدمة متوقفة.
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("تم إيقاف البرنامج يدويًا")
