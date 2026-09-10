import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# 1. Настройки (Вставь сюда СВОИ данные)
BOT_TOKEN = "8945413131:AAGz5xrT9_e9uLd1i2XE8gfzkUWjji469Qc"
# Сюда вставь ссылку на твое приложение в Render (например: https://onrender.com)
RENDER_URL = "https://kiffis-tunell.onrender.com"

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}"

# Включаем логи, чтобы в консоли Render видеть все ошибки
logging.basicConfig(level=logging.INFO)

# 2. Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 3. Твои обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Ура! Я наконец-то работаю на Render через Вебхуки! 🚀🔥")

# Функция, которая сработает при запуске сервера
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Вебхук успешно установлен на: {WEBHOOK_URL}")

def main():
    # Настраиваем вебхук без Flask — через родной aiohttp (это быстрее и надежнее)
    dp.startup.register(on_startup)
    
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)
    
    # Render сам передает порт в переменные окружения, если его нет — берем 8080
    import os
    port = int(os.environ.get("PORT", 8080))
    
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
