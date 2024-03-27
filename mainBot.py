# mainBot.py
from aiogram import Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import bot, TOKEN  # Импортируем bot и TOKEN из config.py
from handlers import register_handlers

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

register_handlers(dp)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
