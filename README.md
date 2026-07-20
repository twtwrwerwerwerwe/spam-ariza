# Telegram CRM Ticket Bot

Umumiy mijozlarga xizmat ko'rsatish uchun Telegram bot. Foydalanuvchilar murojaat
yuboradi, adminlar guruh orqali murojaatlarni qabul qiladi va boshqaradi.

Bu bot hisob tiklash xizmati emas va tashqi platformalarda hech qanday
o'zgarish va'da qilmaydi — u faqat ichki murojaatlarni (tiketlarni) yig'ish va
boshqarish tizimi.

## Texnologiyalar

- Python 3.13+
- aiogram 3.x (Router, FSM, Middleware, Filter)
- SQLite (aiosqlite)
- python-dotenv
- Rotatsion fayl logging

## Loyiha strukturasi

```
telegram_crm_bot/
├── bot/
│   ├── main.py                 # Kirish nuqtasi (Bot, Dispatcher, routerlar)
│   ├── config.py               # .env dan sozlamalarni o'qish
│   ├── handlers/
│   │   ├── common.py           # /start, /cancel
│   │   ├── user.py             # Murojaat yuborish FSM oqimi
│   │   └── admin.py            # Admin panel, tiketlarni qabul qilish
│   ├── database/
│   │   ├── db.py               # Sxema yaratish, ulanish
│   │   └── models.py           # users/tickets/admins/settings so'rovlari
│   ├── keyboards/
│   │   ├── user_kb.py          # Kontakt, kategoriya, asosiy menyu
│   │   └── admin_kb.py         # Admin panel va tiket tugmalari
│   ├── states/
│   │   └── ticket_states.py    # FSM holatlari
│   ├── middlewares/
│   │   ├── throttling.py       # Spamdan himoya
│   │   └── db_middleware.py    # Foydalanuvchini avtomatik ro'yxatga olish, log
│   ├── filters/
│   │   └── admin_filter.py     # IsAdminFilter, IsSuperAdminFilter
│   └── utils/
│       ├── logger.py           # Logging sozlamalari
│       └── export.py           # CSV eksport, DB zaxira nusxa
├── requirements.txt
├── .env.example
└── README.md
```

## O'rnatish

```bash
python3.13 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` faylini oching va quyidagilarni to'ldiring:

```
BOT_TOKEN=<BotFather bergan token>
ADMIN_GROUP_ID=-1003399313219
SUPER_ADMIN_ID=6302873072
DB_PATH=database.db
```

Botni admin guruhga administrator sifatida qo'shing (xabar yuborish va
xabarlarni tahrirlash huquqi bilan) — u yerga yangi murojaatlar tushadi.

## Ishga tushirish

```bash
python -m bot.main
```

Ma'lumotlar bazasi va jadvallar birinchi ishga tushirishda avtomatik
yaratiladi. Loglar `logs/bot.log` fayliga, eksportlar `exports/` papkasiga,
zaxira nusxalar esa `backups/` papkasiga yoziladi.

## Foydalanuvchi oqimi

1. `/start` — salomlashish va ismni so'rash.
2. Telefon raqamini kontakt tugmasi orqali yuborish.
3. Murojaat turini tanlash (6 ta kategoriya).
4. Murojaat bazaga saqlanadi va admin guruhga yuboriladi, foydalanuvchiga
   tasdiq xabari ko'rsatiladi.

## Admin oqimi

- Admin guruhda yangi murojaat xabari ostidagi **✅ Qabul qilish** tugmasi
  bosilganda: murojaat holati yangilanadi, xabar tahrirlanadi va
  foydalanuvchiga bildirishnoma yuboriladi.
- `/admin` — faqat ruxsat etilgan adminlar uchun boshqaruv paneli:
  statistika, foydalanuvchilar, murojaatlar, ommaviy xabar yuborish, admin
  qo'shish/o'chirish (faqat asosiy super-admin), bazani CSV formatda
  eksport qilish va zaxira nusxa olish.

## Muhim eslatma

Bu bot faqat ichki murojaatlarni yig'ish va operatorlarga yo'naltirish uchun
mo'ljallangan. U hech qanday tashqi hisob, xizmat yoki platformada
o'zgartirish, tiklash yoki kafolat bermaydi.
