# Telegram Bot على Render

هذا المشروع يشغّل بوت Telethon مع خادم Flask صغير حتى تتمكن Render من فحص الخدمة عبر `/health`.

## الملفات

| الملف | الغرض |
|---|---|
| `main.py` | كود البوت، خادم HTTP، الإيقاظ الداخلي، والمسار `/health`. |
| `requirements.txt` | مكتبات Python المطلوبة. |
| `render.yaml` | إعداد اختياري لإنشاء خدمة Render تلقائيًا. |
| `.gitignore` | يمنع رفع الأسرار وملفات جلسة Telethon. |

## متغيرات البيئة في Render

أضف القيم التالية من صفحة الخدمة في Render، ولا تضعها داخل GitHub:

| المتغير | القيمة |
|---|---|
| `API_ID` | رقم Telegram API ID. |
| `API_HASH` | Telegram API Hash. |
| `SESSION_STRING` | جلسة Telethon النصية السرية. |
| `ALERT_TARGET` | اسم المستخدم أو معرف الوجهة التي تستقبل التنبيهات. |
| `KEEP_ALIVE_INTERVAL` | اتركه `300`، أي خمس دقائق. |
| `KEEP_ALIVE_URL` | اتركه فارغًا أولًا؛ يستخدم الكود `RENDER_EXTERNAL_URL` تلقائيًا. |

## إعداد Render

استخدم:

```text
Build Command: pip install -r requirements.txt
Start Command: python main.py
Health Check Path: /health
```

بعد النشر افتح:

```text
https://YOUR-SERVICE.onrender.com/health
```

ويجب أن ترى `OK`.

## الإيقاظ الداخلي والخارجي

الإيقاظ الداخلي يرسل طلبًا من العملية نفسها إلى `/health` كل خمس دقائق عندما تكون العملية تعمل. أما الإيقاظ الخارجي فيُنفّذ من خدمة خارجية مثل UptimeRobot؛ أنشئ HTTP Monitor للرابط `/health` بفاصل خمس دقائق. الإيقاظ الداخلي لا يستطيع إعادة تشغيل عملية أوقفتها Render بالكامل، ولذلك يبقى الإيقاظ الخارجي هو الاحتياطي الأفضل.

## الأمان

لا ترفع `API_HASH` أو `SESSION_STRING` أو رمز البوت إلى GitHub. إذا ظهرت هذه القيم في مستودع عام، احذفها وغيّرها فورًا. استخدم مستودعًا خاصًا أو اترك الأسرار داخل Environment Variables في Render فقط.
