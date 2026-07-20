from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

BTN_STATISTICS = "📊 Statistika"
BTN_USERS = "👥 Foydalanuvchilar"
BTN_TICKETS = "📂 Murojaatlar"
BTN_BROADCAST = "📢 Xabar yuborish"
BTN_ADD_ADMIN = "➕ Admin qo'shish"
BTN_REMOVE_ADMIN = "➖ Adminni o'chirish"
BTN_EXPORT = "📁 Bazani eksport qilish"
BTN_BACKUP = "💾 Zaxira nusxa"
BTN_BACK = "🔙 Orqaga"


def get_ticket_inline_keyboard(ticket_id: int, telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Profil", url=f"tg://user?id={telegram_id}"
                ),
                InlineKeyboardButton(
                    text="✅ Qabul qilish", callback_data=f"accept_ticket:{ticket_id}"
                ),
            ]
        ]
    )


def get_admin_panel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_STATISTICS), KeyboardButton(text=BTN_USERS)],
            [KeyboardButton(text=BTN_TICKETS), KeyboardButton(text=BTN_BROADCAST)],
            [KeyboardButton(text=BTN_ADD_ADMIN), KeyboardButton(text=BTN_REMOVE_ADMIN)],
            [KeyboardButton(text=BTN_EXPORT), KeyboardButton(text=BTN_BACKUP)],
        ],
        resize_keyboard=True,
    )


def get_admin_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_BACK)]],
        resize_keyboard=True,
    )


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast_cancel"),
            ]
        ]
    )
