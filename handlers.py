import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import config
import database

router = Router()

# 🧠 Состояния для ввода промокодов и админки
class BotStates(StatesGroup):
    waiting_for_promo = State()
    waiting_for_admin_broadcast = State()

# 🌸 ТЕКСТ ПРИВЕТСТВИЯ
START_TEXT = (
    "⚡️ Добро пожаловать в Kiffis Tunnel!\n\n"
    "Это твой персональный и надёжный доступ к быстрому интернету без ограничений на высокой скорости.\n\n"
    "Наш бот работает на базе Supabase и защищает твои устройства в один клик.\n\n"
    "⭐ Для новых пользователей доступен бесплатный тест на 3 дня (полный доступ)!\n\n"
    "Чтобы настроить подключение, перейди в Личный кабинет по кнопке ниже 👇"
)

# 🎛 НАВЕСНЫЕ КНОПКИ (Внизу экрана)
def get_main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 Личный кабинет", callback_data="open_profile"),
        InlineKeyboardButton(text="🆘 Поддержка", url="https://t.me")
    )
    return builder.as_markup()

# 🐾 ОБРАБОТКА /START И ПРОФИЛЯ
@router.message(Command("start"))
async def cmd_start(message: Message):
    await database.create_user(message.from_user.id, message.from_user.username)
    await message.answer_photo(
        photo=config.PHOTO_MAIN_MENU,
        caption=START_TEXT,
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "open_profile")
async def open_profile(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    user_list = await database.get_user(user_id)
    user = user_list[0] if (user_list and isinstance(user_list, list)) else user_list
    
    status = "🛡 Не защищено / Истекла"
    expire_str = "Отсутствует"
    devices_count = 1
    test_used = True
    
    if user:
        devices_count = user.get("devices", 1)
        test_used = user.get("test_used", True)
        if user.get("expire_date"):
            expire_dt = datetime.fromisoformat(user["expire_date"].replace("Z", "+00:00"))
            if expire_dt.timestamp() > datetime.now().timestamp():
                status = "🛡 Защищено"
                expire_str = expire_dt.strftime("%d.%m.%Y в %H:%M")

    profile_caption = (
        f"⚡️ Kiffis Tunnel | Личный кабинет\n\n"
        f"<b>Пользователь:</b> @{callback.from_user.username or 'User'}\n"
        f"<b>Статус сети:</b> {status}\n"
        f"<b>Период подписки:</b> до {expire_str}\n"
        f"<b>Активных устройств:</b> {devices_count} из 5\n\n"
        f"🪐 Твой персональный ключ доступа готов к работе. Используй меню ниже для управления подпиской, активации промокодов и просмотра инструкций."
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌐 Просто VPN", callback_data="buy_duration:vpn"),
        InlineKeyboardButton(text="🧦 Прокси", callback_data="buy_duration:proxy")
    )
    builder.row(
        InlineKeyboardButton(text="🤍 Белые списки", callback_data="buy_duration:whitelist"),
        InlineKeyboardButton(text="🔄 VPN + БС (Комбо)", callback_data="buy_duration:combo")
    )
    builder.row(
        InlineKeyboardButton(text="📖 Инструкция", url="https://telegra.ph"),
        InlineKeyboardButton(text="🎟 Промокоды", callback_data="promo_enter")
    )
    builder.row(
        InlineKeyboardButton(text="📢 Новости канала", url="https://t.me"),
        InlineKeyboardButton(text="📄 Соглашение", url="https://telegra.ph")
    )
    
    if user and not test_used:
        builder.row(InlineKeyboardButton(text="🎁 Взять бесплатный тест (3 дня)", callback_data="take_free_test"))

    await callback.message.edit_media(
        media=InlineKeyboardBuilder.media_photo(media=config.PHOTO_MAIN_MENU, caption=profile_caption),
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "take_free_test")
async def take_free_test(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_list = await database.get_user(user_id)
    user = user_list[0] if (user_list and isinstance(user_list, list)) else user_list
    
    if user and user.get("test_used", False):
        await callback.answer("❌ Ты уже активировал тестовый период, котик!", show_alert=True)
        return
        
    await database.activate_test_period(user_id)
    await callback.answer("✨ 3 дня бесплатного теста успешно активированы!", show_alert=True)
    await open_profile(callback)

@router.callback_query(F.data == "promo_enter")
async def promo_enter(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer_photo(
        photo=config.PHOTO_PROMO,
        caption="🎟 <b>Активация промокода</b>\n\nУ тебя есть секретный код от Kiffis Tunnel? Отлично!\n\nПросто отправь его следующим сообщением в этот чат. Бот проверит его по базе данных и мгновенно начислит скидку или бонусные дни!"
    )
    await state.set_state(BotStates.waiting_for_promo)

@router.message(BotStates.waiting_for_promo)
async def process_promo(message: Message, state: FSMContext):
    code_text = message.text.strip()
    result = await database.apply_promo(message.from_user.id, code_text)
    await message.answer(result)
    await state.clear()
@router.callback_query(F.data.startswith("buy_duration:"))
async def buy_select_duration(callback: CallbackQuery):
    await callback.answer()
    tariff_type = callback.data.split(":")[1]
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏳ 3 дня", callback_data=f"buy_devs:{tariff_type}:3_days"),
        InlineKeyboardButton(text="📅 1 месяц", callback_data=f"buy_devs:{tariff_type}:1_month"),
        InlineKeyboardButton(text="🗓 3 месяца", callback_data=f"buy_devs:{tariff_type}:3_months")
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="open_profile"))
    
    await callback.message.edit_caption(
        caption="🪐 <b>Выбери срок действия подписки:</b>",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("buy_devs:"))
async def buy_select_devs(callback: CallbackQuery):
    await callback.answer()
    data_parts = callback.data.split(":")
    tariff_type = data_parts[1]
    duration = data_parts[2]
    
    category = "premium" if tariff_type in ["whitelist", "combo"] else "base"
    prices = config.TARIFFS[category][duration]
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"📱 1 устр. (⭐{prices[1]})", callback_data=f"pay:{tariff_type}:{duration}:1"),
        InlineKeyboardButton(text=f"📱 2 устр. (⭐{prices[2]})", callback_data=f"pay:{tariff_type}:{duration}:2")
    )
    builder.row(
        InlineKeyboardButton(text=f"📱 3 устр. (⭐{prices[3]})", callback_data=f"pay:{tariff_type}:{duration}:3"),
        InlineKeyboardButton(text=f"📱 4 устр. (⭐{prices[4]})", callback_data=f"pay:{tariff_type}:{duration}:4")
    )
    builder.row(
        InlineKeyboardButton(text=f"📱 5 устр. (⭐{prices[5]})", callback_data=f"pay:{tariff_type}:{duration}:5")
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад к срокам", callback_data=f"buy_duration:{tariff_type}"))
    
    await callback.message.edit_media(
        media=InlineKeyboardBuilder.media_photo(media=config.PHOTO_TARIFFS, caption="📱 <b>Выбери количество одновременно подключаемых устройств:</b>"),
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("pay:"))
async def checkout(callback: CallbackQuery):
    await callback.answer()
    data_parts = callback.data.split(":")
    tariff_type = data_parts[1]
    duration = data_parts[2]
    devs = int(data_parts[3])
    
    category = "premium" if tariff_type in ["whitelist", "combo"] else "base"
    base_price = config.TARIFFS[category][duration][devs]
    
    user_data = await database.get_user(callback.from_user.id)
    user = user_data if not isinstance(user_data, list) else user_data[0]
    final_price = base_price
    
    if user:
        discount = user.get("active_discount", 0)
        minus_stars = user.get("active_minus_stars", 0)
        if discount > 0:
            if not (discount == 40 and base_price < 50):
                final_price = int(base_price * (1 - discount / 100))
        if minus_stars > 0:
            final_price = base_price - minus_stars
            
    if final_price < 1:
        final_price = 1

    prices = [LabeledPrice(label=f"Подписка {tariff_type}", amount=final_price)]
    
    await callback.message.answer_invoice(
        title="Оплата тарифа Kiffis Tunnel",
        description=f"Тариф: {tariff_type} | Срок: {duration} | Устройств: {devs}",
        prices=prices,
        provider_token="",
        payload=f"{tariff_type}:{duration}:{devs}",
        currency="XTR",
        start_parameter="kiffis_pay"
    )

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    data_parts = payload.split(":")
    tariff_type = data_parts[0]
    duration = data_parts[1]
    devs = int(data_parts[2])
    
    days = 3 if duration == "3_days" else (30 if duration == "1_month" else 90)
    user_data = await database.get_user(message.from_user.id)
    user = user_data if not isinstance(user_data, list) else user_data[0]
    
    current_expire = datetime.fromisoformat(user["expire_date"].replace("Z", "+00:00")) if user and user.get("expire_date") else datetime.now()
    new_expire = max(current_expire, datetime.now()) + timedelta(days=days)
    
    database.supabase.table("users").update({
        "expire_date": new_expire.isoformat(),
        "tariff_type": tariff_type,
        "devices": devs,
        "active_discount": 0,
        "active_minus_stars": 0
    }).eq("user_id", message.from_user.id).execute()
    
    link_to_show = config.URL_AVENCORES_VPN
    if tariff_type == "combo":
        link_to_show = config.URL_AVENCORES_COMBO
    elif tariff_type == "whitelist":
        link_to_show = config.URL_IGARECK_WHITELIST
    elif tariff_type == "proxy":
        link_to_show = await database.assign_free_proxy(message.from_user.id)

    success_caption = (
        "🌟 <b>Оплата прошла успешно! Спасибо за доверие!</b>\n\n"
        "Твоя подписка Kiffis Tunnel активирована.\n\n"
        f"📋 Твоя персональная ссылка-конфиг:\n<code>{link_to_show}</code>\n\n"
        "Нажми на кнопку ниже, чтобы автоматически импортировать настройки в приложение!"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🚀 Подключить в 1 клик", url=link_to_show))
    builder.row(InlineKeyboardButton(text="👤 В личный кабинет", callback_data="open_profile"))
    
    await message.answer_photo(
        photo=config.PHOTO_INSTRUCTIONS,
        caption=success_caption,
        reply_markup=builder.as_markup()
    )

@router.message(Command("panel"))
async def cmd_admin_panel(message: Message):
    if message.from_user.id != config.ADMIN_ID:
        return
        
    stats = await database.get_admin_stats()
    
    admin_caption = (
        "⚙️ <b>ПАНЕЛЬ УПРАВЛЕНИЯ «KIFFIS TUNNEL»</b>\n\n"
        "👥 <b>ПОЛЬЗОВАТЕЛИ:</b>\n"
        f"• Всего в базе: {stats['all']} чел.\n"
        f"• С активной подпиской: {stats['active']} чел.\n"
        f"• Бесплатный тест взяли: {stats['test']} чел.\n\n"
        "🛒 <b>ПОДПИСКИ ПО КАТЕГОРИЯМ:</b>\n"
        f"• Просто VPN: {stats['vpn']} | Прокси: {stats['proxy']}\n"
        f"• Белые списки: {stats['whitelist']} | Комбо: {stats['combo']}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Рассылка новостей", callback_data="admin_broadcast"))
    
    await message.answer(text=admin_caption, reply_markup=builder.as_markup())

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("📢 Отправь текст с картинкой для массовой рассылки всем пользователям:")
    await state.set_state(BotStates.waiting_for_admin_broadcast)

@router.message(BotStates.waiting_for_admin_broadcast)
async def process_admin_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    users_resp = database.supabase.table("users").select("user_id").execute()
    count = 0
    if users_resp.data:
        for u in users_resp.data:
            try:
                await message.copy_to(chat_id=u["user_id"])
                count += 1
                await asyncio.sleep(0.05)
            except Exception:
                pass
    await message.answer(f"✅ Рассылка успешно завершена! Доставлено: {count} пользователям.")

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer_photo(
        photo=config.PHOTO_SUPPORT,
        caption="🆘 <b>Служба поддержки Kiffis Tunnel</b>\n\nЕсли у тебя возникли проблемы с подключением, списанием Telegram Stars или настройкой прокси — не переживай, котик!\n\nНажми на навесную кнопку «🆘 Поддержка» внизу экрана, чтобы написать нашему администратору через безопасный чат."
    )
