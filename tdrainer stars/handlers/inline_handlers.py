# tworksteam/tdrainer stars/handlers/inline_handlers.py

from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

router = Router()

@router.inline_query()
async def inline_mode_handler(query: types.InlineQuery):
    # Проверяем, является ли запрос числом и не пустой ли он
    if not query.query.isdigit() or not query.query:
        return

    amount = int(query.query)
    worker_id = query.from_user.id
    
    # Укажите здесь актуальный юзернейм вашего бота для звёзд
    bot_username = "CheckForStarsBot"

    # ВАЖНО: Добавляем сумму в ссылку после ID воркера
    activate_button = InlineKeyboardButton(
        text="✅ Активировать чек",
        url=f"https://t.me/{bot_username}?start={worker_id}_{amount}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[activate_button]])

    # Формируем текст сообщения, которое будет отправлено
    message_text = f"💳 **Чек на {amount} звёзд**"

    input_content = InputTextMessageContent(
        message_text=message_text,
        parse_mode=ParseMode.MARKDOWN
    )

    result = InlineQueryResultArticle(
        id=str(amount),
        title=f"💳 Создать чек на {amount} звёзд",
        description="Нажмите, чтобы отправить чек пользователю",
        input_message_content=input_content,
        reply_markup=keyboard,
        thumbnail_url="https://i.imgur.com/Al8p2p1.png" # Иконка для чека
    )

    await query.answer(
        results=[result],
        cache_time=1,
        is_personal=True
    )