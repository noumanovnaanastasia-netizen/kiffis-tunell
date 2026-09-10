import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask
from threading import Thread

# 1. Микро-сервер для бесплатного Render
app = Flask('')
@app.route('/')
def home():
    return "OK"

def run():
    app.run(host='0.0.0.0', port=8080)

# 2. Чистый запуск бота
bot = Bot(token="8945413131:AAEoscGljaqoMZoz95CFyiy7OboLT5cheys")
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Ура! Я наконец-то работаю на Render! 🎉")

async def main():
    Thread(target=run).start() # Запуск веб-сервера
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
