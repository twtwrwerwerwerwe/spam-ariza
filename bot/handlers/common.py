from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.user_kb import get_main_menu_keyboard, remove_keyboard
from bot.states.ticket_states import TicketForm

router = Router(name="common")

WELCOME_TEXT = (
    "👋  Assalomu alaykum!\n"
    "💯  Spam bo'lgan bo'lsangiz bizning botimizga murjat yuboring.\n\n"
    "⚡️  Muammoyingizni tez hal qilib beramiz. Eng ishongchi hizmat faqat bizda!"
)

ASK_NAME_TEXT = "👤 Ismingizni kiriting."


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=remove_keyboard())
    await message.answer(ASK_NAME_TEXT)
    await state.set_state(TicketForm.full_name)


@router.message(Command("cancel"))
@router.message(F.text == "❌ Bekor qilish")
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "Hozircha bekor qilinadigan amal yo'q.",
            reply_markup=get_main_menu_keyboard(),
        )
        return
    await state.clear()
    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(F.text == "📩 Murojaat yuborish")
async def restart_ticket_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(ASK_NAME_TEXT, reply_markup=remove_keyboard())
    await state.set_state(TicketForm.full_name)
