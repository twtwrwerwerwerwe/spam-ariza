import logging
import re

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import TICKET_CATEGORIES, config
from bot.database.models import (
    create_ticket,
    get_user_by_telegram_id,
    set_ticket_group_message_id,
    upsert_user,
)
from bot.keyboards.admin_kb import get_ticket_inline_keyboard
from bot.keyboards.user_kb import (
    get_category_keyboard,
    get_main_menu_keyboard,
    get_phone_keyboard,
)
from bot.states.ticket_states import TicketForm

router = Router(name="user")
logger = logging.getLogger(__name__)

ASK_PHONE_TEXT = "📱 Telefon raqamingizni yuboring.\n Hohlasangiz qo'lda yoki tugma orqali yuborishingiz mumkin"
ASK_CATEGORY_TEXT = "📌 Murojaat turini tanlang:"
SUCCESS_TEXT = (
    "✅ Arizangiz yuborildi.\n"
    "Operator tez orada siz bilan bog'lanadi."
)

PHONE_REGEX = re.compile(r"^\+?\d{9,15}$")


@router.message(TicketForm.full_name, F.text.len() > 100)
async def full_name_too_long(message: Message) -> None:
    await message.answer(
        "⚠️ Ism juda uzun. Iltimos, qisqaroq kiriting (maksimum 100 belgi)."
    )


@router.message(TicketForm.full_name, F.text)
async def process_full_name(message: Message, state: FSMContext) -> None:
    full_name = message.text.strip()
    if len(full_name) < 2:
        await message.answer("⚠️ Iltimos, to'liq ismingizni kiriting.")
        return

    await state.update_data(full_name=full_name)
    await message.answer(ASK_PHONE_TEXT, reply_markup=get_phone_keyboard())
    await state.set_state(TicketForm.phone)


@router.message(TicketForm.full_name)
async def full_name_invalid(message: Message) -> None:
    await message.answer("⚠️ Iltimos, ismingizni matn ko'rinishida kiriting.")


@router.message(TicketForm.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"
    await state.update_data(phone=phone)
    await message.answer(
        ASK_CATEGORY_TEXT, reply_markup=get_category_keyboard()
    )
    await state.set_state(TicketForm.category)


@router.message(TicketForm.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if not PHONE_REGEX.match(phone.replace(" ", "")):
        await message.answer(
            "⚠️ Telefon raqami noto'g'ri. Iltimos, '📱 Raqamni yuborish' "
            "tugmasini bosing yoki raqamni +998901234567 ko'rinishida yuboring."
        )
        return

    await state.update_data(phone=phone)
    await message.answer(
        ASK_CATEGORY_TEXT, reply_markup=get_category_keyboard()
    )
    await state.set_state(TicketForm.category)


@router.message(TicketForm.phone)
async def phone_invalid(message: Message) -> None:
    await message.answer(
        "⚠️ Iltimos, telefon raqamingizni tugma orqali yuboring yoki matn "
        "ko'rinishida kiriting."
    )


@router.message(TicketForm.category, F.text.in_(TICKET_CATEGORIES))
async def process_category(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    full_name = data.get("full_name", "-")
    phone = data.get("phone", "-")
    category = message.text
    telegram_user = message.from_user

    await upsert_user(
        telegram_id=telegram_user.id,
        full_name=full_name,
        phone=phone,
        username=telegram_user.username,
    )
    user_row = await get_user_by_telegram_id(telegram_user.id)

    ticket_id = await create_ticket(
        user_id=user_row["id"],
        telegram_id=telegram_user.id,
        full_name=full_name,
        phone=phone,
        category=category,
    )

    admin_text = (
        "🆕 YANGI ZAKAZ TEZ ALOQAGA CHIQING\n\n"
        f"👤 Ism: {full_name}\n\n"
        f"📱 Telefon: {phone}\n\n"
        f"📌 MUAMMO: {category}\n\n"
        f"🆔 Telegram ID: {telegram_user.id}\n\n"
        f"_________________________________\n\n"
        f"🔢 Murojaat raqami: #{ticket_id}"
    )

    try:
        sent_message = await bot.send_message(
            chat_id=config.admin_group_id,
            text=admin_text,
            reply_markup=get_ticket_inline_keyboard(ticket_id, telegram_user.id),
        )
        await set_ticket_group_message_id(ticket_id, sent_message.message_id)
    except Exception:
        logger.exception(
            "Murojaatni admin guruhga yuborishda xatolik: ticket_id=%s", ticket_id
        )

    await message.answer(SUCCESS_TEXT, reply_markup=get_main_menu_keyboard())
    await state.clear()


@router.message(TicketForm.category)
async def category_invalid(message: Message) -> None:
    await message.answer(
        "⚠️ Iltimos, quyidagi tugmalardan birini tanlang.",
        reply_markup=get_category_keyboard(),
    )
