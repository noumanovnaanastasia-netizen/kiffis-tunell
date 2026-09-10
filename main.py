from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I am alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

import config
import database
import handlers

# 📝 Настраиваем логи, чтобы видеть ошибки в панели Render
logging.basicConfig(level=logging.INFO)

# 🧙‍♂️ Создаем объекты бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# 🌐 Крошечный веб-сервер для прохождения проверок Render.com (Port Timeout Fix)
async def handle_web_request(request):
    return web.Response(text="Kiffis Tunnel is Live! 🐱🌸")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_web_request)
    runner = web.AppRunner(app)
    await runner.setup()
    # Считываем порт, который Render выдает автоматически
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port}")

# 🚀 Главная функция запуска всего проекта
async def main():
    # 🗄 1. Запускаем автоматическое создание таблиц в Supabase
    logging.info("Initializing database tables...")
    await database.init_database()
    
    # 🎛 2. Подключаем обработчики кнопок
    dp.include_router(handlers.router)
    
    # 🌐 3. Запускаем веб-сервер для Render
    await start_web_server()
    
    # 🧹 4. Удаляем старые вебхуки и запускаем Long Polling
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Kiffis Tunnel Bot started successfully!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()  # Запускаем веб-сервер для Render
    asyncio.run(main())  # Запускаем вашего бота

