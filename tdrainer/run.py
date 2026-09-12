# twork/tdrainer/run.py

import asyncio
import logging
from bot_instance import dp, bot
from handlers.user_handlers import router as user_handlers_router
from handlers.business_handlers import router as business_handlers_router
from handlers.inline_handlers import router as inline_handlers_router
from handlers.manual_control_handlers import router as manual_control_router
from database import init_db

async def main() -> None:
    init_db()

    dp.include_router(user_handlers_router)
    dp.include_router(business_handlers_router)
    dp.include_router(inline_handlers_router)
    dp.include_router(manual_control_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Дрейнер-бот запускается...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")