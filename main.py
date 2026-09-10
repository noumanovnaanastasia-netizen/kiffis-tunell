 import os
import random
import logging
import asyncio
from datetime import datetime, timedelta
import aiohttp

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)

# --- НАСТРОЙКИ (Из переменных окружения Koyeb) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- ЖИВЫЕ ССЫЛКИ НА ГИТХАБ (ПЛАН Б) ---
URLS = {
    "vpn": "https://githubusercontent.com",
    "proxy": "https://githubusercontent.com",
    "whitelist": "https://githubusercontent.com",
    "combo": "https://githubusercontent.com" 
}

# --- ФИНАЛЬНАЯ ТАРИФНАЯ СЕТКА КИФИС ---
TARIFS = {
    "vpn": {
        "3d": {"name": "3 дня", "days": 3, "rub": 10, "stars": 7},
        "14d": {"name": "14 дней", "days": 14, "rub": 30, "stars": 20},
        "1m": {"name": "1 месяц", "days": 30, "rub": 45, "stars": 30},
        "2m": {"name": "2 месяца", "days": 60, "rub": 90, "stars": 42},
        "3m": {"name": "3 месяца", "days": 90, "rub": 140, "stars": 70},
    },
    "proxy": {
        "3d": {"name": "3 дня", "days": 3, "rub": 10, "stars": 7},
        "14d": {"name": "14 дней", "days": 14, "rub": 30, "stars": 20},
        "1m": {"name": "1 месяц", "days": 30, "rub": 45, "stars": 30},
        "2m": {"name": "2 месяца", "days": 60, "rub": 90, "stars": 42},
        "3m": {"name": "3 месяца", "days": 90, "rub": 140, "stars": 70},
    },
    "whitelist": {
        "3d": {"name": "3 дня", "days": 3, "rub": 15, "stars": 10},
        "14d": {"name": "14 дней", "days": 14, "rub": 40, "stars": 25},
        "1m": {"name": "1 месяц", "days": 30, "rub": 60, "stars": 36},
        "2m": {"name": "2 месяца", "days": 60, "rub": 120, "stars": 60},
        "3m": {"name": "3 месяца", "days": 90, "rub": 190, "stars": 80},
    },
    "combo": {
        "3d": {"name": "3 дня", "days": 3, "rub": 15, "stars": 10},
        "14d": {"name": "14 дней", "days": 14, "rub": 40, "stars": 25},
        "1m": {"name": "1 месяц", "days": 30, "rub": 60, "stars": 36},
        "2m": {"name": "2 месяца", "days": 60, "rub": 120, "stars": 60},
        "3m": {"name": "3 месяца", "days": 90, "rub": 190, "stars": 80},
    }
}

NAMES = {"vpn": "🌐 Просто VPN", "proxy": "🧦 Прокси", "whitelist": "🤍 Белые списки", "combo": "🔄 VPN + БС"}

# --- ФУНКЦИИ БАЗЫ ДАННЫХ ---
def db_init_user(uid: int):
    try:
        res = supabase.table("users").select("*").eq("user_id", uid).execute()
        if not res.data:
            supabase.table("users").insert({"user_id": uid}).execute()
    except Exception as e:
        logging.error(f"DB Init Error: {e}")

def db_get_user(uid: int):
    try:
        res = supabase.table("users").select("*").eq("user_id", uid).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logging.error(f"DB Get Error: {e}")
        return None

# --- ВЫДАЧА КЛЮЧЕЙ (ПРИОРИТЕТ ТВОИМ ПРОКСИ) ---
async def fetch_vpn_key(service_type: str):
    if service_type == "proxy":
        try:
            res = supabase.table("my_proxy").select("*").eq("is_used", False).order("id").limit(1).execute()
            if res.data:
                item = res.data[0]
                supabase.table("my_proxy").update({"is_used": True}).eq("id", item["id"]).execute()
                return item["proxy_key"]
        except Exception as e:
            logging.error(f"Error reading my_proxy table: {e}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(URLS[service_type]) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    valid_keys = [l for l in lines if not l.startswith("#")]
                    if service_type == "combo":
                        hysteria = [k for k in valid_keys if k.startswith("hysteria2://")]
                        return random.choice(hysteria) if hysteria else random.choice(valid_keys)
                    return random.choice(valid_keys)
    except Exception as e:
        logging.error(f"GitHub Error: {e}")
    return "vless://error_database_unreachable_try_again_later"
# --- ИНТЕРФЕЙС И КЛАВИАТУРЫ ---
def main_menu():
    b = InlineKeyboardBuilder()
    b.button(text="👤 Мой профиль", callback_data="m_profile")
    b.button(text="💳 Купить подписку", callback_data="m_buy")
    b.button(text="📚 Инструкция", callback_data="m_info")
    b.adjust(1)
    return b.as_markup()

@dp.message(Command("start"))
async def start(m: types.Message):
    db_init_user(m.from_user.id)
    await m.answer(
        "🦊 *Добро пожаловать в Kiffis Tunnel!*\n\n"
        "Мы создаем твой персональный защищенный туннель, внутри которого "
        "работают сразу 4 передовые технологии для полной свободы в сети.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "m_profile")
async def profile(c: types.CallbackQuery):
    db_init_user(c.from_user.id)
    u = db_get_user(c.from_user.id)
    now = datetime.now()
    
    if not u:
        await c.answer("Ошибка профиля, попробуй еще раз через /start", show_alert=True)
        return

    def parse_exp(val):
        if not val: return "❌ Не активна"
        dt = datetime.fromisoformat(val.replace("Z", "+00:00")).replace(tzinfo=None)
        if dt > now:
            return f"✅ Активна (до {dt.strftime('%d.%m.%Y %H:%M')})"
        return "❌ Истекла"

    txt = (
        f"👤 *Твой профиль в Kiffis Tunnel:*\n\n"
        f"💰 Баланс: {u['balance']} Stars\n\n"
        f"🌐 Просто VPN: {parse_exp(u['vpn_expires'])}\n`{u['vpn_key'] or ''}`\n\n"
        f"🧦 Прокси: {parse_exp(u['proxy_expires'])}\n`{u['proxy_key'] or ''}`\n\n"
        f"🤍 Белые списки: {parse_exp(u['whitelist_expires'])}\n`{u['whitelist_key'] or ''}`\n\n"
        f"🔄 VPN + БС: {parse_exp(u['combo_expires'])}\n`{u['combo_key'] or ''}`\n\n"
        f"📌 _Нажми на нужный ключ выше, чтобы мгновенно скопировать его._"
    )
    await c.message.edit_text(txt, parse_mode="Markdown", reply_markup=main_menu())

@dp.callback_query(F.data == "m_info")
async def info(c: types.CallbackQuery):
    txt = (
        "🤖 *Подробный мануал Kiffis Tunnel*\n\n"
        "📑 *Что означают разделы?*\n"
        "• *Просто VPN (Умный обход)* — включает защиту только на заблокированных сайтах (Инстаграм, Ютуб). Сбер и Госуслуги работают напрямую без потери скорости.\n"
        "• *Прокси (Быстрый доступ)* — выделенная линия. Можно вставить прямо в настройки Telegram или Discord, чтобы они летали отдельно от всего телефона.\n"
        "• *Белые списки (Полный обход)* — шифрует вообще весь трафик на телефоне. Пробивает самые жесткие блокировки.\n"
        "• *VPN + БС (Максимальное комбо)* — тариф «Всё включено». Микс из протоколов VLESS и Hysteria2. Если заблокируют один — второй подхватит работу незаметно!\n\n"
        "💳 *Как купить и оплатить?*\n"
        "1. Перейди в меню «Купить подписку».\n"
        "2. Новичкам советуем нажать «🆓 1 день (Тест)» — ключ выдается бесплатно!\n"
        "3. Для платных сроков выбери способ оплаты: *Telegram Stars* (в 1 клик прямо в приложении) или *Рубли по СБП* (переведи деньги админу и отправь скриншот чека в этот чат).\n\n"
        "📱 *Как настроить на телефоне?*\n"
        "• *Для iPhone:* Скачай приложение **v2box** или **Hiddify** из App Store. Скопируй ключ из профиля бота, в приложении нажми «+» ➡️ *Import from Clipboard*. Нажми большую кнопку подключения!\n"
        "• *Для Android:* Скачай приложение **v2rayNG** или **Hiddify** из Google Play. Скопируй ключ. В v2rayNG нажми «+» ➡️ *Импорт профиля из буфера обмена*. Нажми круглую кнопку подключения внизу."
    )
    await c.message.edit_text(txt, parse_mode="Markdown", reply_markup=main_menu())

# --- ПОКУПКА ---
@dp.callback_query(F.data == "m_buy")
async def buy_types(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    for k, v in NAMES.items():
        b.button(text=v, callback_data=f"type_{k}")
    b.button(text="↩️ Назад", callback_data="back_main")
    b.adjust(1)
    await c.message.edit_text("Какую секцию нашего туннеля ты хочешь настроить или купить?", reply_markup=b.as_markup())

@dp.callback_query(F.data == "back_main")
async def back_m(c: types.CallbackQuery):
    await c.message.edit_text("Главное меню Kiffis Tunnel:", reply_markup=main_menu())

@dp.callback_query(F.data.startswith("type_"))
async def buy_durations(c: types.CallbackQuery):
    stype = c.data.split("_")[1]
    db_init_user(c.from_user.id)
    u = db_get_user(c.from_user.id)
    
    b = InlineKeyboardBuilder()
    if u and not u[0]["has_used_test"]:
        b.button(text="🆓 1 день (Тест - БЕСПЛАТНО)", callback_data=f"dur_{stype}_test")
        
    for duration, data in TARIFS[stype].items():
        b.button(text=f"{data['name']} — {data['rub']}₽ / {data['stars']}⭐", callback_data=f"dur_{stype}_{duration}")
    b.button(text="↩️ Назад", callback_data="m_buy")
    b.adjust(1)
    await c.message.edit_text(f"Выбери период подписки для *{NAMES[stype]}*:", parse_mode="Markdown", reply_markup=b.as_markup())

@dp.callback_query(F.data.startswith("dur_"))
async def pay_method(c: types.CallbackQuery):
    _, stype, duration = c.data.split("_")
    
    if duration == "test":
        db_init_user(c.from_user.id)
        u = db_get_user(c.from_user.id)
        if u and u[0]["has_used_test"]:
            await c.answer("Ты уже активировала бесплатный тест!", show_alert=True)
            return
        
        key = await fetch_vpn_key(stype)
        exp = (datetime.now() + timedelta(days=1)).isoformat()
        supabase.table("users").update({
            f"{stype}_expires": exp,
            f"{stype}_key": key,
            "has_used_test": True
        }).eq("user_id", c.from_user.id).execute()
        
        await c.message.answer(f"🎉 Тестовый период Kiffis Tunnel на 1 день активирован!\n🔑 Твой ключ:\n`{key}`", parse_mode="Markdown")
        await c.answer()
        return

    b = InlineKeyboardBuilder()
    b.button(text="⭐ Telegram Stars", callback_data=f"pay_stars_{stype}_{duration}")
    b.button(text="🇷🇺 Рубли (СБП)", callback_data=f"pay_rub_{stype}_{duration}")
    b.button(text="↩️ Назад", callback_data=f"type_{stype}")
    b.adjust(1)
    await c.message.edit_text("Выбери удобный способ оплаты подписки:", reply_markup=b.as_markup())

# --- ИНВОЙСЫ STARS ---
@dp.callback_query(F.data.startswith("pay_stars_"))
async def stars_invoice(c: types.CallbackQuery):
    _, _, stype, duration = c.data.split("_")
    data = TARIFS[stype][duration]
    
    await bot.send_invoice(
        chat_id=c.from_user.id,
        title=f"{NAMES[stype]}",
        description=f"Kiffis Tunnel - Подписка на {data['name']}",
        payload=f"stars_{stype}_{duration}",
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice(label="Покупка туннеля", amount=data["stars"])]
    )
    await c.answer()

@dp.pre_checkout_query()
async def checkout(pc: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pc.id, ok=True)

@dp.message(F.successful_payment)
async def success_stars(m: types.Message):
    _, stype, duration = m.successful_payment.invoice_payload.split("_")
    days = TARIFS[stype][duration]["days"]
    
    key = await fetch_vpn_key(stype)
    exp = (datetime.now() + timedelta(days=days)).isoformat()
    
    supabase.table("users").update({
        f"{stype}_expires": exp,
        f"{stype}_key": key
    }).eq("user_id", m.from_user.id).execute()
    
    await m.answer(f"🎉 Успешная оплата Звёздами!\nТвой {NAMES[stype]} активирован на {days} дней.\n🔑 Ключ:\n`{key}`", parse_mode="Markdown")

# --- ОПЛАТА РУБЛЯМИ ---
@dp.callback_query(F.data.startswith("pay_rub_"))
async def rub_instruction(c: types.CallbackQuery):
    _, _, stype, duration = c.data.split("_")
    data = TARIFS[stype][duration]
    
    await c.message.answer(
        f"🇷🇺 *Оплата СБП ({data['name']}):*\n\n"
        f"1. Переведи *{data['rub']} рублей* по СБП на карту.\n"
        f"2. Номер телефона: `+79991112233` (Т-Банк, Твое Имя).\n"
        f"3. Сделай скриншот чека и *отправь его фото прямо сюда в чат с ботом*.",
        parse_mode="Markdown"
    )
    await c.answer()

@dp.message(F.photo)
async def forward_receipt(m: types.Message):
    uid = m.from_user.id
    b = InlineKeyboardBuilder()
    b.button(text="✅ Одобрить", callback_data=f"adm_ok_{uid}")
    b.button(text="❌ Отклонить", callback_data=f"adm_no_{uid}")
    b.adjust(2)
    
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=m.photo[-1].file_id,
        caption=f"🔔 *Новый чек от @{m.from_user.username}* (ID: `{uid}`). Какую команду выполнить?",
        parse_mode="Markdown",
        reply_markup=b.as_markup()
    )
    await m.answer("📥 Твой чек переслан администратору Kiffis Tunnel. Подписка будет выдана сразу после проверки!")

# --- АДМИН-ОДОБРЕНИЕ ---
@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(c: types.CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        return
        
    _, action, target_uid = c.data.split("_")
    target_uid = int(target_uid)
    
    if action == "ok":
        key = await fetch_vpn_key("vpn")
        exp = (datetime.now() + timedelta(days=30)).isoformat()
        
        supabase.table("users").update({
            "vpn_expires": exp,
            "vpn_key": key
        }).eq("user_id", target_uid).execute()
        
        await bot.send_message(target_uid, f"🥳 Твой чек успешно проверен! Доступ к Kiffis Tunnel открыт на 30 дней.\n🔑 Ключ:\n`{key}`", parse_mode="Markdown")
        await c.message.edit_caption(caption=c.message.caption + "\n\n🟢 Одобрено!")
    else:
        await bot.send_message(target_uid, "❌ Твой чек был отклонен. Проверь сумму перевода или свяжись с поддержкой.")
        await c.message.edit_caption(caption=c.message.caption + "\n\n🔴 Отклонено.")
    await c.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
