import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiohttp import web
import config
from handlers import router
import database as db

# Включаем логирование, чтобы видеть подробный отчет о работе в консоли Render
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и главный диспетчер
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Подключаем наши модули с кнопками и командами к диспетчеру
dp.include_router(router)

async def handle_ping(request):
    """Служебный обработчик для Render, показывающий, что сервер живой"""
    return web.Response(text="Kiffis Tunnel Online! 🦊")

async def main():
    # 1. Запуск микро-веб-сервера «заглушки» на фоне для обмана Render
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Берем порт, который выдает Render, если его нет — ставим 8080
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"🚀 Служебный веб-сервер успешно открыт на порту {port}")

    # 2. Первичная проверка и автоматическая заливка промокодов в Supabase
    await db.init_database()
    logging.info("🗄 База данных Supabase успешно проверена!")

    # 3. Запуск чтения сообщений из Telegram (Long Polling)
    # Очищаем очередь сообщений, скопившихся, пока бот был выключен
    await bot.delete_webhook(drop_pending_updates=True)
    
    logging.info("🦊 Бот Kiffis Tunnel успешно запущен и слушает команды...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запускаем наш главный асинхронный цикл
    asyncio.run(main())
