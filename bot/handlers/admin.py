import asyncio
import logging
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import (
    TICKET_STATUS_ACCEPTED,
    TICKET_STATUS_NEW,
    config,
)
from bot.database.models import (
    accept_ticket,
    add_admin,
    count_tickets,
    count_tickets_by_status,
    count_tickets_today,
    count_users,
    get_all_admins,
    get_all_users,
    get_ticket,
    get_tickets_by_status,
    is_admin,
    remove_admin,
)
from bot.filters.admin_filter import IsAdminFilter, IsSuperAdminFilter
from bot.keyboards.admin_kb import (
    BTN_ADD_ADMIN,
    BTN_BACK,
    BTN_BACKUP,
    BTN_BROADCAST,
    BTN_EXPORT,
    BTN_REMOVE_ADMIN,
    BTN_STATISTICS,
    BTN_TICKETS,
    BTN_USERS,
    get_admin_cancel_keyboard,
    get_admin_panel_keyboard,
    get_broadcast_confirm_keyboard,
)
from bot.states.ticket_states import AddAdminForm, BroadcastForm, RemoveAdminForm
from bot.utils.export import backup_database, export_tickets_to_csv, export_users_to_csv

router = Router(name="admin")
logger = logging.getLogger(__name__)

ADMIN_PANEL_TEXT = "🛠 Admin panelga xush kelibsiz. Kerakli bo'limni tanlang."


# ---------------------------------------------------------------------------
# Panel entry
# ---------------------------------------------------------------------------

@router.message(Command("admin"), IsAdminFilter())
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(ADMIN_PANEL_TEXT, reply_markup=get_admin_panel_keyboard())


@router.message(F.text == BTN_BACK, IsAdminFilter())
async def admin_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(ADMIN_PANEL_TEXT, reply_markup=get_admin_panel_keyboard())


# ---------------------------------------------------------------------------
# Ticket acceptance (admin group)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("accept_ticket:"))
async def on_accept_ticket(callback: CallbackQuery, bot: Bot) -> None:
    admin_user = callback.from_user
    if not await is_admin(admin_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q.", show_alert=True)
        return

    ticket_id = int(callback.data.split(":", 1)[1])
    ticket = await get_ticket(ticket_id)
    if ticket is None:
        await callback.answer("⚠️ Murojaat topilmadi.", show_alert=True)
        return

    if ticket["status"] != TICKET_STATUS_NEW:
        await callback.answer("ℹ️ Bu murojaat allaqachon qabul qilingan.", show_alert=True)
        return

    admin_username = f"@{admin_user.username}" if admin_user.username else admin_user.full_name
    success = await accept_ticket(ticket_id, admin_user.id, admin_username)
    if not success:
        await callback.answer("ℹ️ Bu murojaat allaqachon qabul qilingan.", show_alert=True)
        return

    accepted_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_text = (
        "✅ Murojaat qabul qilindi\n\n"
        f"👤 Ism: {ticket['full_name']}\n"
        f"📱 Telefon: {ticket['phone']}\n"
        f"📌 Kategoriya: {ticket['category']}\n"
        f"🆔 Telegram ID: {ticket['telegram_id']}\n"
        f"🔢 Murojaat raqami: #{ticket_id}\n\n"
        f"👨‍💼 Admin: {admin_username}\n"
        f"🕒 Vaqt: {accepted_time}"
    )

    try:
        await callback.message.edit_text(new_text, reply_markup=None)
    except Exception:
        logger.exception("Murojaat xabarini tahrirlashda xatolik: ticket_id=%s", ticket_id)

    try:
        await bot.send_message(
            chat_id=ticket["telegram_id"],
            text="✅ Sizning murojaatingiz operator tomonidan qabul qilindi.",
        )
    except Exception:
        logger.exception(
            "Foydalanuvchiga xabar yuborishda xatolik: telegram_id=%s",
            ticket["telegram_id"],
        )

    await callback.answer("✅ Murojaat siz tomoningizdan qabul qilindi.")


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

@router.message(F.text == BTN_STATISTICS, IsAdminFilter())
async def show_statistics(message: Message) -> None:
    total_users = await count_users()
    total_tickets = await count_tickets()
    new_tickets = await count_tickets_by_status(TICKET_STATUS_NEW)
    accepted_tickets = await count_tickets_by_status(TICKET_STATUS_ACCEPTED)
    today_tickets = await count_tickets_today()

    text = (
        "📊 STATISTIKA\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"📂 Jami murojaatlar: {total_tickets}\n"
        f"🆕 Yangi murojaatlar: {new_tickets}\n"
        f"✅ Qabul qilingan murojaatlar: {accepted_tickets}\n"
        f"📅 Bugungi murojaatlar: {today_tickets}"
    )
    await message.answer(text)


# ---------------------------------------------------------------------------
# Users list
# ---------------------------------------------------------------------------

@router.message(F.text == BTN_USERS, IsAdminFilter())
async def show_users(message: Message) -> None:
    users = await get_all_users()
    total = len(users)
    if total == 0:
        await message.answer("👥 Hozircha foydalanuvchilar mavjud emas.")
        return

    lines = [f"👥 FOYDALANUVCHILAR (jami: {total})\n"]
    for user in users[:30]:
        username = f"@{user['username']}" if user.get("username") else "—"
        lines.append(
            f"• {user.get('full_name') or '—'} | {user.get('phone') or '—'} | "
            f"{username} | ID: {user['telegram_id']}"
        )
    if total > 30:
        lines.append(f"\n... va yana {total - 30} ta foydalanuvchi.")
    await message.answer("\n".join(lines))


# ---------------------------------------------------------------------------
# Tickets list
# ---------------------------------------------------------------------------

@router.message(F.text == BTN_TICKETS, IsAdminFilter())
async def show_tickets(message: Message) -> None:
    new_tickets = await get_tickets_by_status(TICKET_STATUS_NEW, limit=20)
    if not new_tickets:
        await message.answer("📂 Hozircha yangi murojaatlar yo'q.")
        return

    lines = [f"📂 YANGI MUROJAATLAR (so'nggi {len(new_tickets)} ta)\n"]
    for ticket in new_tickets:
        lines.append(
            f"#{ticket['id']} | {ticket['full_name']} | {ticket['phone']} | "
            f"{ticket['category']} | {ticket['created_at']}"
        )
    await message.answer("\n".join(lines))


# ---------------------------------------------------------------------------
# Broadcast
# ---------------------------------------------------------------------------

@router.message(F.text == BTN_BROADCAST, IsAdminFilter())
async def start_broadcast(message: Message, state: FSMContext) -> None:
    await message.answer(
        "📢 Yubormoqchi bo'lgan xabar matnini kiriting.",
        reply_markup=get_admin_cancel_keyboard(),
    )
    await state.set_state(BroadcastForm.waiting_for_message)


@router.message(BroadcastForm.waiting_for_message, F.text == BTN_BACK)
async def cancel_broadcast_input(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(ADMIN_PANEL_TEXT, reply_markup=get_admin_panel_keyboard())


@router.message(BroadcastForm.waiting_for_message, F.text)
async def receive_broadcast_text(message: Message, state: FSMContext) -> None:
    await state.update_data(broadcast_text=message.text)
    await message.answer(
        f"Quyidagi xabar barcha foydalanuvchilarga yuborilsinmi?\n\n{message.text}",
        reply_markup=get_broadcast_confirm_keyboard(),
    )
    await state.set_state(BroadcastForm.waiting_for_confirmation)


@router.callback_query(F.data == "broadcast_cancel", BroadcastForm.waiting_for_confirmation)
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Xabar yuborish bekor qilindi.")
    await callback.answer()


@router.callback_query(F.data == "broadcast_confirm", BroadcastForm.waiting_for_confirmation)
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()
    await callback.message.edit_text("⏳ Xabar yuborilmoqda...")

    users = await get_all_users()
    sent = 0
    failed = 0
    for user in users:
        try:
            await bot.send_message(chat_id=user["telegram_id"], text=text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await callback.message.answer(
        f"✅ Xabar yuborildi.\n\n📨 Yuborildi: {sent}\n⚠️ Yuborilmadi: {failed}",
        reply_markup=get_admin_panel_keyboard(),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Add admin (super admin only)
# ---------------------------------------------------------------------------

@router.message(
    F.text == BTN_ADD_ADMIN,
    IsSuperAdminFilter(config.super_admin_id),
)
async def start_add_admin(message: Message, state: FSMContext) -> None:
    await message.answer(
        "➕ Yangi admin Telegram ID raqamini kiriting.",
        reply_markup=get_admin_cancel_keyboard(),
    )
    await state.set_state(AddAdminForm.waiting_for_id)


@router.message(AddAdminForm.waiting_for_id, F.text == BTN_BACK)
async def cancel_add_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(ADMIN_PANEL_TEXT, reply_markup=get_admin_panel_keyboard())


@router.message(AddAdminForm.waiting_for_id, F.text)
async def finish_add_admin(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamlardan iborat Telegram ID kiriting.")
        return

    new_admin_id = int(message.text.strip())
    success = await add_admin(new_admin_id, added_by=message.from_user.id)
    await state.clear()

    if success:
        await message.answer(
            f"✅ Admin qo'shildi: {new_admin_id}",
            reply_markup=get_admin_panel_keyboard(),
        )
    else:
        await message.answer(
            f"⚠️ Bu foydalanuvchi allaqachon admin: {new_admin_id}",
            reply_markup=get_admin_panel_keyboard(),
        )


# ---------------------------------------------------------------------------
# Remove admin (super admin only)
# ---------------------------------------------------------------------------

@router.message(
    F.text == BTN_REMOVE_ADMIN,
    IsSuperAdminFilter(config.super_admin_id),
)
async def start_remove_admin(message: Message, state: FSMContext) -> None:
    admins = await get_all_admins()
    if not admins:
        await message.answer("ℹ️ Hozircha qo'shimcha adminlar mavjud emas.")
        return

    lines = ["➖ O'chirmoqchi bo'lgan admin Telegram ID raqamini kiriting.\n"]
    for admin in admins:
        lines.append(f"• {admin['telegram_id']}")
    await message.answer("\n".join(lines), reply_markup=get_admin_cancel_keyboard())
    await state.set_state(RemoveAdminForm.waiting_for_id)


@router.message(RemoveAdminForm.waiting_for_id, F.text == BTN_BACK)
async def cancel_remove_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(ADMIN_PANEL_TEXT, reply_markup=get_admin_panel_keyboard())


@router.message(RemoveAdminForm.waiting_for_id, F.text)
async def finish_remove_admin(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamlardan iborat Telegram ID kiriting.")
        return

    target_id = int(message.text.strip())
    success = await remove_admin(target_id)
    await state.clear()

    if success:
        await message.answer(
            f"✅ Admin o'chirildi: {target_id}",
            reply_markup=get_admin_panel_keyboard(),
        )
    else:
        await message.answer(
            f"⚠️ Bunday admin topilmadi: {target_id}",
            reply_markup=get_admin_panel_keyboard(),
        )


# ---------------------------------------------------------------------------
# Export & backup
# ---------------------------------------------------------------------------

@router.message(F.text == BTN_EXPORT, IsAdminFilter())
async def export_database(message: Message) -> None:
    await message.answer("⏳ Ma'lumotlar eksport qilinmoqda...")
    users_file = await export_users_to_csv()
    tickets_file = await export_tickets_to_csv()

    await message.answer_document(FSInputFile(users_file), caption="👥 Foydalanuvchilar ro'yxati")
    await message.answer_document(FSInputFile(tickets_file), caption="📂 Murojaatlar ro'yxati")


@router.message(F.text == BTN_BACKUP, IsAdminFilter())
async def backup_db(message: Message) -> None:
    await message.answer("⏳ Zaxira nusxa tayyorlanmoqda...")
    backup_path = backup_database()
    await message.answer_document(
        FSInputFile(backup_path), caption="💾 Ma'lumotlar bazasi zaxira nusxasi"
    )
