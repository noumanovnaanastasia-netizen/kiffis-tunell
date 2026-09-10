import os
import logging
import asyncio
import httpx
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import PreCheckoutQuery, ContentType
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка конфигурации из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# HTTP-клиент для работы с Supabase API
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Ссылки на живой репозиторий с конфигами (План Б)
GITHUB_CONFIGS_URL = "https://githubusercontent.com"

# Цены и тарифы (План: Дни -> (Цена в Stars, Название))
TARIFFS = {
    "vpn_proxy": {
        "1": (0, "1 день (Тест)"),
        "3": (7, "3 дня"),
        "14": (20, "14 дней"),
        "30": (30, "1 месяц"),
        "62": (42, "2 месяца"),
        "90": (70, "3 месяца"),
    },
    "white_combo": {
        "1": (0, "1 день (Тест)"),
        "3": (10, "3 дня"),
        "14": (25, "14 дней"),
        "30": (36, "1 месяц"),
        "62": (60, "2 месяца"),
        "90": (80, "3 месяца"),
    }
}

# --- Вспомогательные функции для Supabase ---
async def get_or_create_user(user_id: int, username: str):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{SUPABASE_URL}/rest/v1/users?telegram_id=eq.{user_id}", headers=HEADERS)
            users = res.json()
            if not users:
                new_user = {"telegram_id": user_id, "username": username, "is_test_used": False, "subscription_until": None}
                await client.post(f"{SUPABASE_URL}/rest/v1/users", headers=HEADERS, json=new_user)
                return new_user
            return users[0]
        except Exception as e:
            logging.error(f"Ошибка БД: {e}")
            return {"is_test_used": False}

async def mark_test_used(user_id: int):
    async with httpx.AsyncClient() as client:
        await client.patch(f"{SUPABASE_URL}/rest/v1/users?telegram_id=eq.{user_id}", headers=HEADERS, json={"is_test_used": True})

async def get_secret_proxy():
    """ План А: Берем из таблицы my_proxy """
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{SUPABASE_URL}/rest/v1/my_proxy?is_used=eq.false&limit=1", headers=HEADERS)
            proxies = res.json()
            if proxies:
                proxy = proxies[0]
                # Гасим ключ
                await client.patch(f"{SUPABASE_URL}/rest/v1/my_proxy?id=eq.{proxy['id']}", headers=HEADERS, json={"is_used": True})
                return proxy["proxy_string"]
        except Exception as e:
            logging.error(f"Ошибка извлечения прокси: {e}")
    return None

async def get_github_fallback_config():
    """ План Б: Если ключи кончились, парсим GitHub """
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(GITHUB_CONFIGS_URL)
            if res.status_code == 200:
                lines = res.text.splitlines()
                for line in lines:
                    if line.strip() and not line.startswith("#"):
                        return line.strip()
    except Exception as e:
        logging.error(f"Ошибка загрузки с GitHub: {e}")
    return "Извините, свободных ключей временно нет. Обратитесь к админу!"

# --- Хэндлеры Бота ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await get_or_create_user(message.from_user.id, message.from_user.username)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Просто VPN", callback_data="cat_vpn")
    kb.button(text="🧦 Прокси", callback_data="cat_proxy")
    kb.button(text="🤍 Белые списки", callback_data="cat_white")
    kb.button(text="🔄 VPN + БС (Комбо)", callback_data="cat_combo")
    kb.adjust(2)
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! Добро пожаловать в **Kiffis Tunnel 🦊**.\n"
        f"Выбери необходимую услугу в меню ниже:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("cat_"))
async def choose_tariff(callback: types.CallbackQuery):
    category = callback.data.split("_")[1] # vpn, proxy, white, combo
    pool = "white_combo" if category in ["white", "combo"] else "vpn_proxy"
    
    user = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    
    kb = InlineKeyboardBuilder()
    for days, (stars, label) in TARIFFS[pool].items():
        if days == "1" and user.get("is_test_used"):
            continue # Пропускаем бесплатный тест, если уже использован
        kb.button(text=f"{label} — {stars} ⭐", callback_data=f"buy_{category}_{days}_{stars}")
    
    kb.button(text="💳 Оплата в рублях (СБП)", callback_data=f"sbp_{category}")
    kb.button(text="⬅ Назад", callback_data="back_to_main")
    kb.adjust(1)
    
    await callback.message.edit_text("Выбери срок подписки (Оплата через Telegram Stars):", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.delete()
    await cmd_start(callback.message)

# --- Оплата через Telegram Stars ---
@dp.callback_query(F.data.startswith("buy_"))
async def process_stars_payment(callback: types.CallbackQuery):
    _, category, days, stars = callback.data.split("_")
    stars = int(stars)
    
    if stars == 0: # Бесплатный тест
        await mark_test_used(callback.from_user.id)
        key = await get_secret_proxy() or await get_github_fallback_config()
        await callback.message.answer(f"🎉 Ваш тестовый доступ активирован!\n\nВаш ключ доступа:\n`{key}`", parse_mode="Markdown")
        await callback.answer()
        return

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Подписка {category.upper()}",
        description=f"Активация доступа на {days} дней.",
        payload=f"{category}_{days}_{callback.from_user.id}",
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice(label="Оплата подписки", amount=stars)]
    )
    await callback.answer()

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    category, days, user_id = payload.split("_")
    
    key = await get_secret_proxy() or await get_github_fallback_config()
    await message.answer(
        f"🔥 Спасибо за оплату! Подписка на {days} дней успешно оформлена.\n\n"
        f"Ваш персональный ключ конфигурации:\n`{key}`", 
        parse_mode="Markdown"
    )

# --- Ручная оплата по СБП ---
@dp.callback_query(F.data.startswith("sbp_"))
async def sbp_instruction(callback: types.CallbackQuery):
    await callback.message.answer(
        "ℹ **Инструкция для оплаты по СБП:**\n\n"
        "1. Переведите сумму на карту/телефон администратора.\n"
        "2. Отправьте **СКРИНШОТ/ФОТО ЧЕКА** прямо в этот чат.\n"
        "3. Мы проверим перевод и сразу вышлем вам ключ!",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(F.photo)
async def handle_receipt(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Одобрить", callback_data=f"admin_approve_{message.from_user.id}")
    kb.button(text="❌ Отклонить", callback_data=f"admin_decline_{message.from_user.id}")
    kb.adjust(2)
    
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=f"🔔 **Новый чек на проверку!**\nОт: @{message.from_user.username} (ID: {message.from_user.id})",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await message.answer("⏳ Чек отправлен на проверку администратору. Ожидайте уведомления!")

@dp.callback_query(F.data.startswith("admin_"))
async def process_admin_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав!", show_alert=True)
        return
        
    action, _, user_id = callback.data.split("_")[1:]
    user_id = int(user_id)
    
    if action == "approve":
        key = await get_secret_proxy() or await get_github_fallback_config()
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 Администратор одобрил ваш платеж по СБП!\n\nВаш ключ доступа:\n`{key}`",
            parse_mode="Markdown"
        )
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n🟢 Одобрено!")
    else:
        await bot.send_message(
            chat_id=user_id,
            text="❌ Ваш чек был отклонен администратором. Проверьте данные или свяжитесь с поддержкой."
        )
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n🔴 Отклонено.")
    await callback.answer()

# --- Веб-сервер для прохождения проверки Render ---
async def web_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Kiffis Tunnel is running! 🦊"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
