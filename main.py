import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# 1. Твой токен от @KIFFISST_BOT
BOT_TOKEN = "8945413131:AAEoscGljaqoMZoz95CFyiy7OboLT5cheys"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Ура! Я наконец-то ожил и работаю на Render! 🚀🤖\nГотова создавать кибер-империю?")

# Микро-сервер для обмана Render (чтобы он видел активный порт)
async def handle_ping(request):
    return web.Response(text="Бот онлайн!")

async def main():
    # Запуск веб-сервера на фоне
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Сервер-заглушка успешно запущен на порту {port}")

    # Запуск самого бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
