# Telegram Userbot على Render

هذا المشروع يشغّل يوزربوت Telegram باستخدام **Telethon** وواجهة Flask بسيطة لتوفير مسار فحص صحي يمكن استخدامه مع Render وcron-job.org أو UptimeRobot.

يدعم ملف `main.py` تشغيل **ثلاثة حسابات Telegram داخل خدمة Render واحدة**. كل حساب يستخدم بيانات API وجلسة مستقلة، وإذا فشلت جلسة واحدة فإن الجلسات الأخرى تستمر في العمل.

> لا تضع أي `API_HASH` أو `SESSION_STRING` داخل GitHub. أضف جميع القيم السرية من Environment Variables داخل Render فقط.

## الملفات

| الملف | الغرض |
| --- | --- |
| `main.py` | الكود الرئيسي، تشغيل الحسابات الثلاثة، التصفية، التحويل، وواجهة Flask. |
| `requirements.txt` | مكتبات Python المطلوبة للتشغيل. |
| `render.yaml` | إعدادات خدمة Render الاختيارية. |
| `.gitignore` | منع رفع الملفات السرية أو الملفات المؤقتة. |

## ميزة التصفية

لا يحوّل البوت كل الرسائل. يجب أن تتحقق الرسالة من الشروط التالية معًا:

1. وجود كلمة مفتاحية أو عبارة مساعدة مثل `يساعدني` أو `يحل` أو `يسوي` أو `أحد يساعد`.

1. عدم وجود كلمة من قائمة الكلمات المستبعدة.

1. وجود كلمة مطلوبة واحدة على الأقل، مثل `واجب` أو `بحث` أو `مشروع` أو `تقرير` أو `ترجمة` أو `تصميم` أو `بوربوينت`.

كما يتجاهل البوت رسائل الوجهة المحددة في `ALERT_TARGET` ومعرفات المجموعة الموجودة داخل الكود، حتى لا يعيد تحويل الرسائل إلى المصدر نفسه.

## متغيرات البيئة في Render

افتح خدمة Render ثم اذهب إلى:

```
Environment → Environment Variables
```

أضف المتغيرات التالية. اكتب الاسم في خانة **Key** والقيمة الحقيقية في خانة **Value**.

| Key | Value |
| --- | --- |
| `API_ID_1` | رقم API ID للحساب الأول |
| `API_HASH_1` | API Hash للحساب الأول |
| `SESSION_STRING_1` | String Session للحساب الأول |
| `API_ID_2` | رقم API ID للحساب الثاني |
| `API_HASH_2` | API Hash للحساب الثاني |
| `SESSION_STRING_2` | String Session للحساب الثاني |
| `API_ID_3` | رقم API ID للحساب الثالث |
| `API_HASH_3` | API Hash للحساب الثالث |
| `SESSION_STRING_3` | String Session للحساب الثالث |
| `ALERT_TARGET` | اسم الوجهة المشتركة، مثل `Aymen8642` |

يجب أن تكون المطابقة بين البيانات بهذا الشكل:

```
API_ID_1 + API_HASH_1 + SESSION_STRING_1 = الحساب الأول
API_ID_2 + API_HASH_2 + SESSION_STRING_2 = الحساب الثاني
API_ID_3 + API_HASH_3 + SESSION_STRING_3 = الحساب الثالث
```

لا تخلط بيانات الحسابات. لا تستخدم `API_HASH_1` مع `SESSION_STRING_2`، ولا تستخدم جلسة واحدة في حسابين أو خدمتين مختلفتين.

إذا أردت تشغيل حساب واحد أو حسابين فقط، اترك مجموعة الحساب غير المستخدم فارغة أو احذفها بالكامل. لكن عند استخدام أي حساب يجب إضافة بياناته الثلاثة: `API_ID` و`API_HASH` و`SESSION_STRING` الخاصة به.

## المتغيرات القديمة التي لا يستخدمها هذا الإصدار

لا تضف هذه المتغيرات القديمة؛ لأنها ليست مطلوبة في النسخة الحالية:

```
API_ID
API_HASH
SESSION_STRING
KEEP_ALIVE_INTERVAL
KEEP_ALIVE_URL
```

يتم توفير الإيقاظ الخارجي عن طريق فحص مسار `/health` من cron-job.org أو UptimeRobot.

## إعداد Render

أنشئ Web Service جديدة أو افتح الخدمة الحالية، ثم استخدم الإعدادات التالية:

```
Language: Python 3
Branch: telegram_bot
Root Directory: فارغ
Build Command: pip install -r requirements.txt
Start Command: python main.py
Instance Type: Free
```

إذا كان `render.yaml` مستخدمًا، فيجب أن تكون إعداداته قريبة من التالي:

```yaml
services:
  - type: web
    name: telegram-render-bot
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    healthCheckPath: /health
```

لا تضع الأسرار داخل `render.yaml`. أضفها من لوحة Render فقط.

## ملف requirements.txt

يجب أن يحتوي الملف على المكتبات التالية:

```
Telethon
Flask
Gunicorn
```

يُستخدم أمر التشغيل `python main.py`، ولذلك لا تستخدم أمر Django مثل `gunicorn your_application.wsgi`.

## النشر من GitHub

بعد استبدال `main.py` ورفع التغييرات إلى الفرع `telegram_bot`، اضغط **Commit changes** في GitHub.

إذا كان **Auto-Deploy** مفعّلًا في Render، فسيبدأ النشر تلقائيًا بعد وصول Commit الجديد. وإذا كان معطلًا، افتح Render واضغط:

```
Manual Deploy → Deploy latest commit
```

بعد تغيير Environment Variables اضغط **Save Changes**، ثم انتظر إعادة تشغيل الخدمة أو نفّذ النشر اليدوي إذا لم يبدأ تلقائيًا.

## التحقق من الخدمة

بعد نجاح النشر افتح:

```
https://YOUR-SERVICE.onrender.com/health
```

استبدل `YOUR-SERVICE` باسم خدمة Render الحقيقي. النتيجة الصحيحة هي:

```
OK
```

كما يمكن فتح الرابط الرئيسي:

```
https://YOUR-SERVICE.onrender.com/
```

والنتيجة المتوقعة:

```
I am alive!
```

## الإيقاظ الخارجي

لإرسال طلب فحص كل خمس دقائق، أنشئ مهمة في cron-job.org أو UptimeRobot باستخدام:

```
URL: https://YOUR-SERVICE.onrender.com/health
Method: GET
Interval: Every 5 minutes
```

يجب أن يعيد الرابط حالة HTTP ناجحة ومحتوى `OK`.

## سلوك فشل الجلسات

كل جلسة تعمل في مهمة مستقلة. إذا حدث خطأ مؤقت في الحساب الثاني، يحاول الكود إعادة الاتصال بعد فترة قصيرة، بينما تستمر الجلسة الأولى والثالثة.

إذا ظهر الخطأ التالي:

```
AuthKeyDuplicatedError
```

فهذا يعني أن جلسة الحساب المعني استُخدمت من مكان آخر أو لم تعد صالحة. يتوقف هذا الحساب فقط، وتستمر بقية الحسابات. الحل هو إنشاء `SESSION_STRING` جديدة لذلك الحساب وتحديث المتغير المناسب في Render، مثلًا `SESSION_STRING_2`.

## الأمان

لا ترفع القيم التالية إلى مستودع GitHub عام أو خاص:

```
API_HASH_1
API_HASH_2
API_HASH_3
SESSION_STRING_1
SESSION_STRING_2
SESSION_STRING_3
```

إذا ظهرت إحدى هذه القيم في Commit أو لقطة شاشة أو رسالة، احذفها وأنشئ قيمة جديدة عند الحاجة. كذلك لا تشارك Render API Key أو أي مفاتيح وصول في المحادثات العامة.

## إيقاف الخدمة مؤقتًا

إذا أردت إيقاف البوت أثناء التعديل، استخدم من Render خيار:

```
Suspend Service
```

وبعد الانتهاء استخدم:

```
Resume
```

ثم تحقق من نجاح النشر وافتح مسار `/health` مرة أخرى.
