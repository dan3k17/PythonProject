import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from handlers import registration  # Основной роутер с регистрацией и меню
from database.db import on_startup, on_shutdown

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Инициализация диспетчера с хранилищем в памяти
dp = Dispatcher(storage=MemoryStorage())


async def main():
    # Запуск базы данных
    on_startup()

    # Подключение роутеров
    dp.include_router(registration.router)

    # Удаление вебхука и пропуск необработанных обновлений
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        # Запуск бота
        logging.info("Бот успешно запущен!")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
    finally:
        # Завершение работы и закрытие соединений
        on_shutdown()
        await bot.session.close()
        logging.info("Бот остановлен.")


if __name__ == "__main__":
    asyncio.run(main())