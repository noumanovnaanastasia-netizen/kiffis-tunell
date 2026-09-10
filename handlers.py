import datetime
from aiogram import Router, types, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config
import database as db

router = Router()

# Состояния для ввода текста администратором и пользователями (FSM)
class BotStates(StatesGroup):
    waiting_for_promo = State()
    waiting_for_broadcast = State()
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()
    waiting_for_custom_promo = State()
    waiting_for_admin_give_id = State()

def get_main_menu():
    """Стильное главное меню из 4 рядов по твоему макету"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Просто VPN", callback_data="service_base_vpn")
    builder.button(text="🧦 Прокси", callback_data="service_base_proxy")
    builder.button(text="🤍 Белые списки", callback_data="service_premium_whitelist")
    builder.button(text="🔄 VPN + БС (Комбо)", callback_data="service_premium_combo")
    builder.button(text="📖 Инструкция", callback_data="menu_instruction")
    builder.button(text="🎟 Промокоды", callback_data="menu_promo")
    builder.button(text="🆘 Помощь", callback_data="menu_support")
    builder.button(text="📄 Соглашение", callback_data="menu_agreement")
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()

# --- БЛОКИРОВКА ПОЛЬЗОВАТЕЛЕЙ (ПРОВЕРКА) ---
@router.message()
async def check_ban_middleware(message: types.Message, next_handler=None):
    user = await db.get_user(message.from_user.id)
    if user and user.get("is_banned"):
        await message.answer("🛑 Ваш доступ к боту и серверам заблокирован администрацией.")
        return
    if next_handler:
        await next_handler(message)

# --- КОМАНДА /START ---
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await db.register_user(message.from_user.id, message.from_user.username)
    
    # Показываем красивое приветствие с котиком/тюленем из канала @banerss777
    await message.answer_photo(
        photo=config.PHOTO_MAIN_MENU,
        caption=(
            f"🦊 **Добро пожаловать в Kiffis Tunnel, {message.from_user.first_name}!**\n\n"
            "Стабильный и безопасный доступ нового поколения. Обход блокировок в 2 клика! 📱\n\n"
            "Управляйте подпиской и выбирайте услуги с помощью интуитивного меню ниже 👇"
        ),
        reply_markup=get_main_menu()
    )

# --- ИНФОРМАЦИОННЫЕ КНОПКИ ---
@router.callback_query(F.data == "menu_agreement")
async def show_agreement(callback: types.CallbackQuery):
    await callback.message.answer(f"📄 **Пользовательское соглашение и правила:**\n{config.URL_AGREEMENT}")
    await callback.answer()

@router.callback_query(F.data == "menu_instruction")
async def show_instruction(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🍏 Инструкция для iOS", url=config.URL_INSTR_IOS)
    builder.button(text="🤖 Инструкция для Android", url=config.URL_INSTR_ANDROID)
    builder.adjust(1)
    await callback.message.answer_photo(
        photo=config.PHOTO_INSTRUCTIONS,
        caption="📖 Выберите платформу для просмотра подробного пошагового руководства по подключению:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "menu_support")
async def show_support(callback: types.CallbackQuery):
    await callback.message.answer_photo(
        photo=config.PHOTO_SUPPORT,
        caption="🆘 **Возникли вопросы или перебои со связью?**\n\nНе стесняйтесь обращаться в нашу службу поддержки! Напишите нашему официальному саппорт-аккаунту, и мы поможем решить любую проблему."
    )
    await callback.answer()
# --- ПОШАГОВЫЙ ИНТЕРФЕЙС ТАРИФОВ (СРОК ➡️ УСТРОЙСТВА) ---
@router.callback_query(F.data.startswith("service_"))
async def process_service_choice(callback: types.CallbackQuery):
    _, tarif_class, service_type = callback.data.split("_")
    user_data = await db.get_user(callback.from_user.id)
    
    builder = InlineKeyboardBuilder()
    
    # Если тест еще не использован — выводим кнопку бесплатного периода
    if user_data and not user_data.get("used_trial"):
        builder.button(text="🎁 Взять тест 3 дня бесплатно! (0 ⭐)", callback_data=f"trial_{service_type}")
        
    builder.button(text="📅 3 Дня", callback_data=f"time_{tarif_class}_{service_type}_3days")
    builder.button(text="📅 14 Дней", callback_data=f"time_{tarif_class}_{service_type}_14days")
    builder.button(text="📅 1 Месяц", callback_data=f"time_{tarif_class}_{service_type}_1month")
    builder.button(text="📅 3 Месяца", callback_data=f"time_{tarif_class}_{service_type}_3months")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    builder.adjust(1)
    
    await callback.message.edit_media(
        media=types.InputMediaPhoto(media=config.PHOTO_TARIFFS, caption="📅 **Шаг 1: Выберите срок действия подписки**\nЧем больше выбранный период, тем выгоднее итоговая стоимость!"),
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("time_"))
async def process_time_choice(callback: types.CallbackQuery):
    _, tarif_class, service_type, duration = callback.data.split("_")
    
    builder = InlineKeyboardBuilder()
    
    # Генерируем 5 кнопок устройств с ценами из config.py
    for i in range(1, 6):
        if duration == "14days":
            # Расчитываем 14 дней как среднее между 3д и 1м
            p_3d = config.TARIFFS[tarif_class]["3_days"][i]
            p_1m = config.TARIFFS[tarif_class]["1_month"][i]
            price = int((p_3d + p_1m) / 2)
        else:
            duration_key = "3_days" if duration == "3days" else "1_month" if duration == "1month" else "3_months"
            price = config.TARIFFS[tarif_class][duration_key][i]
            
        builder.button(text=f"📱 {i} устр. — {price} ⭐", callback_data=f"buy_{service_type}_{duration}_{i}_{price}")
        
    builder.button(text="🔙 Назад к срокам", callback_data=f"service_{tarif_class}_{service_type}")
    builder.adjust(1)
    
    await callback.message.edit_caption(
        caption="⬇️ **Шаг 2: Выберите количество одновременно подключаемых устройств**\nЦена указана за весь выбранный пакет со скидкой:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# --- АКТИВАЦИЯ ТЕСТА НА 3 ДНЯ ---
@router.callback_query(F.data.startswith("trial_"))
async def process_trial(callback: types.CallbackQuery):
    service_type = callback.data.split("_")
    user_id = callback.from_user.id
    
    user_data = await db.get_user(user_id)
    if user_data and user_data.get("used_trial"):
        await callback.message.answer("🛑 Вы уже использовали свой тестовый период!")
        await callback.answer()
        return
        
    end_date = (datetime.datetime.now() + datetime.timedelta(days=3)).strftime("%d.%m.%Y")
    await db.activate_trial(user_id, end_date)
    
    await callback.message.answer(
        f"🎉 **Тестовый период успешно активирован!**\n\n"
        f"📋 Ваша подписка: Комбо (VPN + Белые списки)\n"
        f"📅 Действует до: {end_date}\n"
        f"🔑 Ссылка на пул конфигов:\n`{config.URL_AVENCORES_VPN}`"
    )
    await callback.answer()

# --- ВЫСТАВЛЕНИЕ СЧЕТА В TELEGRAM STARS ---
@router.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery, bot: Bot):
    _, service_type, duration, devices, price = callback.data.split("_")
    price = int(price)
    
    prices = [types.LabeledPrice(label="Покупка VPN/Прокси", amount=price)]
    
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Подписка {service_type.upper()}",
        description=f"Пакет услуг на {duration} для {devices} устр.",
        provider_token="", # Для Stars токен должен быть пустым
        currency="XTR",
        prices=prices,
        payload=f"{service_type}_{duration}_{devices}"
    )
    await callback.answer()

# --- ОБРАБОТКА ОПЛАТЫ STARS ---
@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    service_type, duration, devices = payload.split("_")
    
    days = 3 if duration == "3days" else 14 if duration == "14days" else 30 if duration == "1month" else 90
    end_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%d.%m.%Y")
    
    await db.add_subscription(message.from_user.id, end_date, service_type)
    
    pool_url = config.URL_AVENCORES_VPN if service_type in ["vpn", "combo"] else config.URL_IGARECK_WHITELIST
    await message.answer(
        f"✨ **Оплата прошла успешно! Благодарим за покупку!** ✨\n\n"
        f"📋 Тариф: {service_type.upper()} ({devices} устройств)\n"
        f"📅 Срок действия: до {end_date}\n"
        f"🔑 Ваш персональный ключ туннеля:\n`{pool_url}`"
    )

# --- ПРОМОКОДЫ ---
@router.callback_query(F.data == "menu_promo")
async def promo_click(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_promo)
    await callback.message.answer_photo(
        photo=config.PHOTO_PROMO,
        caption="🎟 **Активация авторских промокодов**\n\nВведите ваш секретный промокод в текстовом поле ниже, чтобы получить скидку или бонусные дни подписки:"
    )
    await callback.answer()

@router.message(StateFilter(BotStates.waiting_for_promo))
async def promo_entered(message: types.Message, state: FSMContext):
    code_text = message.text.strip()
    promo = await db.get_promocode(code_text)
    
    if not promo:
        await message.answer("❌ Такого промокода не существует или он написан с ошибкой.")
        await state.clear()
        return
        
    uses = promo["uses"]
    if uses <= 0:
        await message.answer("❌ К сожалению, данный промокод уже исчерпал все свои активации.")
        await state.clear()
        return
        
    p_type = promo["type"]
    val = promo["value"]
    
    if p_type == "bonus_days":
        end_date = (datetime.datetime.now() + datetime.timedelta(days=int(val))).strftime("%d.%m.%Y")
        await db.add_subscription(message.from_user.id, end_date, "combo")
        await db.decrease_promo_uses(code_text, uses)
        await message.answer(f"🎉 Промокод успешно активирован! Вам начислено {val} дней бесплатного Комбо-доступа до {end_date}!")
    elif p_type in ["percent", "stars", "percent_condition"]:
        await message.answer(f"🎟 Код принят! Вы получили купон на скидку в {val}. Она применится автоматически при следующей генерации счета на оплату услуг.")
    
    await state.clear()

# --- ВОЗВРАТ В МЕНЮ ---
@router.callback_query(F.data == "back_to_main")
async def back_main(callback: types.CallbackQuery):
    await callback.message.edit_media(
        media=types.InputMediaPhoto(media=config.PHOTO_MAIN_MENU, caption="🦊 **Главное меню Kiffis Tunnel**\nВыберите нужную опцию:"),
        reply_markup=get_main_menu()
    )
    await callback.answer()
# ==================== СЕКРЕТНАЯ АДМИН-ПАНЕЛЬ ====================
@router.message(Command("panel"))
async def admin_panel(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
        
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Рассылка новостей", callback_data="adm_broadcast")
    builder.button(text="🛑 Забанить юзера", callback_data="adm_ban")
    builder.button(text="🟢 Разбанить юзера", callback_data="adm_unban")
    builder.button(text="🎟 Создать промокод", callback_data="adm_new_promo")
    builder.button(text="🎮 Выдача (Крестики-Нолики)", callback_data="adm_give_menu")
    builder.adjust(1)
    
    await message.answer("👑 **Секретная панель управления Kiffis Tunnel**\n\nВыберите действие администратора:", reply_markup=builder.as_markup())

# 📢 Админ-рассылка
@router.callback_query(F.data == "adm_broadcast")
async def adm_broad(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_broadcast)
    await callback.message.answer("📢 Пришлите текст и картинку для массовой рассылки всем пользователям:")
    await callback.answer()

@router.message(StateFilter(BotStates.waiting_for_broadcast))
async def do_broadcast(message: types.Message, state: FSMContext, bot: Bot):
    users = await db.get_all_users()
    count = 0
    for uid in users:
        try:
            if message.photo:
                await bot.send_photo(chat_id=uid, photo=message.photo[-1].file_id, caption=message.caption)
            else:
                await bot.send_message(chat_id=uid, text=message.text)
            count += 1
        except Exception:
            pass
    await message.answer(f"✅ Рассылка успешно завершена. Сообщение получили {count} человек.")
    await state.clear()

# 🎟 Создание промокода в боте
@router.callback_query(F.data == "adm_new_promo")
async def adm_new_pr(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_custom_promo)
    await callback.message.answer("Введите параметры промокода через пробел:\n`КОД` `тип(bonus_days/percent/stars)` `значение` `активации` \n\nПример: `NEWYEAR bonus_days 10 5`")
    await callback.answer()

@router.message(StateFilter(BotStates.waiting_for_custom_promo))
async def save_custom_promo(message: types.Message, state: FSMContext):
    try:
        code, p_type, val, uses = message.text.split()
        await db.create_new_promocode(code, p_type, int(val), int(uses))
        await message.answer(f"✅ Промокод `{code}` успешно внесен в базу данных Supabase и готов к использованию!")
    except Exception:
        await message.answer("❌ Ошибка формата. Попробуйте еще раз.")
    await state.clear()

# 🛑 Блокировка
@router.callback_query(F.data == "adm_ban")
async def adm_b(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_ban_id)
    await callback.message.answer("💬 Введите Telegram ID пользователя для блокировки:")
    await callback.answer()

@router.message(StateFilter(BotStates.waiting_for_ban_id))
async def do_ban(message: types.Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
        await db.update_user_ban(uid, True)
        await message.answer(f"✅ Пользователь `{uid}` успешно заблокирован.")
    except Exception:
        await message.answer("❌ Ошибка ввода ID.")
    await state.clear()

# 🟢 Разблокировка
@router.callback_query(F.data == "adm_unban")
async def adm_ub(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_unban_id)
    await callback.message.answer("💬 Введите Telegram ID пользователя для разблокировки:")
    await callback.answer()

@router.message(StateFilter(BotStates.waiting_for_unban_id))
async def do_unban(message: types.Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
        await db.update_user_ban(uid, False)
        await message.answer(f"✅ Пользователь `{uid}` успешно разблокирован.")
    except Exception:
        await message.answer("❌ Ошибка ввода ID.")
    await state.clear()

# 🎮 Интерактивная выдача ("Крестики-нолики")
@router.callback_query(F.data == "adm_give_menu")
async def give_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_admin_give_id)
    await callback.message.answer("💬 Введите Telegram ID пользователя, которому хотите выдать подписку:")
    await callback.answer()

@router.message(StateFilter(BotStates.waiting_for_admin_give_id))
async def generate_tic_tac(message: types.Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
        builder = InlineKeyboardBuilder()
        builder.button(text="🌐 VPN [❌]", callback_data=f"tictac_{uid}_vpn_yes")
        builder.button(text="🧦 Прокси [❌]", callback_data=f"tictac_{uid}_proxy_yes")
        builder.button(text="🤍 Белые Списки [❌]", callback_data=f"tictac_{uid}_whitelist_yes")
        builder.button(text="💾 Подтвердить выдачу", callback_data=f"tictacsave_{uid}_combo")
        builder.adjust(1)
        
        await message.answer(f"🎮 **Панель выдачи для ID: {uid}**\nКликайте по кнопкам, чтобы включить нужные услуги:", reply_markup=builder.as_markup())
    except Exception:
        await message.answer("❌ Неверный ID.")
    await state.clear()

@router.callback_query(F.data.startswith("tictac_"))
async def tictac_click(callback: types.CallbackQuery):
    _, uid, service, status = callback.data.split("_")
    new_status = "yes" if status == "no" else "no"
    char = "✅" if status == "yes" else "❌"
    
    # Динамически переключаем кнопки в "Крестики-Нолики"
    builder = InlineKeyboardBuilder()
    builder.button(text=f"{service.upper()} [{char}]", callback_data=f"tictac_{uid}_{service}_{new_status}")
    builder.button(text="💾 Подтвердить выдачу", callback_data=f"tictacsave_{uid}_{service}")
    builder.adjust(1)
    
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("tictacsave_"))
async def tictac_save(callback: types.CallbackQuery):
    _, uid, service = callback.data.split("_")
    end_date = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime("%d.%m.%Y")
    await db.add_subscription(int(uid), end_date, service)
    await callback.message.answer(f"💾 Подписка на {service.upper()} для пользователя `{uid}` успешно обновлена в базе данных до {end_date}!")
    await callback.answer()
