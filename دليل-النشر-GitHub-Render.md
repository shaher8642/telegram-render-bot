# دليل رفع البوت إلى GitHub وربطه بـ Render

## الملفات المطلوبة

ارفع إلى جذر مستودع GitHub هذه الملفات:

```text
main.py
requirements.txt
render.yaml
.gitignore
README.md
```

لا ترفع `API_HASH` أو `SESSION_STRING` أو أي رمز سري.

## إنشاء مستودع GitHub

افتح [github.com/new](https://github.com/new)، اكتب اسمًا مثل `telegram-bot-render`، اختر **Private** ثم اضغط **Create repository**. داخل المستودع اختر **Add file > Upload files** وارفع الملفات الخمسة من الحزمة، ثم اضغط **Commit changes**. تأكد من أن `main.py` و`requirements.txt` موجودان في جذر المستودع وليس داخل مجلد إضافي.

## إنشاء خدمة Render

افتح [dashboard.render.com](https://dashboard.render.com)، اختر **New + > Web Service**، اربط GitHub، ثم اختر المستودع. اضبط الحقول كما يلي:

| الحقل | القيمة |
|---|---|
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python main.py` |
| Plan | `Free` |
| Health Check Path | `/health` |

يمكنك استخدام `render.yaml` بدل إدخال أوامر البناء والتشغيل يدويًا، لكن أدخل الأسرار يدويًا في Environment Variables.

## إضافة Environment Variables

من صفحة الخدمة اختر **Environment** ثم أضف:

| الاسم | القيمة |
|---|---|
| `API_ID` | رقم Telegram API ID. |
| `API_HASH` | Telegram API Hash. |
| `SESSION_STRING` | StringSession السرية. |
| `ALERT_TARGET` | اسم المستخدم أو معرف وجهة التنبيهات. |
| `KEEP_ALIVE_INTERVAL` | `300`. |
| `KEEP_ALIVE_URL` | اتركه فارغًا أولًا؛ سيستخدم الكود `RENDER_EXTERNAL_URL` تلقائيًا. |

لا تضف `PORT`؛ Render تضبطه تلقائيًا. اضغط **Save Changes** ثم **Manual Deploy > Deploy latest commit** إذا لم يبدأ النشر تلقائيًا.

## اختبار Render

بعد النشر انسخ رابط الخدمة، مثل:

```text
https://telegram-bot-render.onrender.com
```

افتح:

```text
https://telegram-bot-render.onrender.com/health
```

يجب أن تظهر `OK`. ثم راجع **Logs** وابحث عن:

```text
Userbot started — listening...
```

## إعداد الإيقاظ الخارجي

افتح [uptimerobot.com](https://uptimerobot.com)، أنشئ حسابًا، ثم اختر **Add New Monitor**. استخدم الإعدادات التالية:

| الحقل | القيمة |
|---|---|
| Monitor Type | `HTTP(s)` |
| Friendly Name | `Telegram Bot Render` |
| URL | رابط الخدمة متبوعًا بـ `/health` |
| Monitoring Interval | `5 minutes` |

مثال الرابط:

```text
https://telegram-bot-render.onrender.com/health
```

الإيقاظ الداخلي في `main.py` يحاول طلب `/health` كل خمس دقائق طالما أن العملية تعمل. أما UptimeRobot فيرسل الطلب من خارج Render، ولذلك هو الجزء المهم عند محاولة تقليل السكون.

## حدود الحل

الإيقاظ الداخلي لا يستطيع إعادة تشغيل البوت إذا أوقفت Render العملية بالكامل؛ لأن الكود نفسه يكون متوقفًا. والإيقاظ الخارجي يقلل السكون، لكنه لا يضمن 24/7 عند إعادة التشغيل أو تعليق الخدمة أو تغيير سياسة الخطة المجانية.

## حل الأخطاء

إذا ظهر `ModuleNotFoundError` فتأكد من وجود `requirements.txt` في جذر المستودع وأعد النشر. إذا ظهر أن `API_ID` أو `SESSION_STRING` مفقود، أضفه في Environment داخل Render. إذا فشل `/health`، راجع Logs وتأكد من أن Start Command هو `python main.py`. إذا فشل تسجيل Telethon، أنشئ جلسة جديدة وتأكد من نسخ `SESSION_STRING` كاملة دون مسافات أو أسطر إضافية.

## الأمان

اجعل المستودع **Private**. لا تضع الأسرار في GitHub أو UptimeRobot. إذا نشرت `SESSION_STRING` بالخطأ، ألغِ الجلسة وأنشئ StringSession جديدة فورًا.

## المراجع

[1]: https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository "GitHub: Adding a file to a repository"
[2]: https://render.com/docs/web-services "Render: Web Services"
[3]: https://render.com/docs/deploy-flask "Render: Deploy a Flask App"
[4]: https://render.com/docs/free "Render: Deploy for Free"
