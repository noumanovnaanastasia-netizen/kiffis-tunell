from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, PROMOCODES_STARTUP

# Инициализируем официальный клиент Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def init_database():
    """
    Первичная проверка базы данных.
    Если таблица промокодов пустая, мы автоматически загружаем туда 
    твой стартовый набор PROMOCODES_STARTUP из config.py.
    """
    try:
        res = supabase.table("promocodes").select("*").limit(1).execute()
        if not res.data:
            for code, data in PROMOCODES_STARTUP.items():
                supabase.table("promocodes").insert({
                    "code": code,
                    "type": data["type"],
                    "value": data["value"],
                    "uses": data["uses"]
                }).execute()
    except Exception:
        # Если таблицы еще не созданы в панели Supabase, пропускаем, чтобы бот не падал
        pass

async def register_user(user_id: int, username: str):
    """
    Регистрация нового пользователя при команде /start.
    По умолчанию: не забанен (False), тест не использован (False), подписки нет (None).
    """
    res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not res.data:
        user_data = {
            "user_id": user_id,
            "username": username if username else "NoUsername",
            "subscription_end": None,
            "used_trial": False,
            "is_banned": False,
            "active_services": "none"  # Может быть: vpn, proxy, whitelist, combo
        }
        supabase.table("users").insert(user_data).execute()

async def get_user(user_id: int):
    """Получение полной карточки пользователя по его ID"""
    res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    return res.data[0] if res.data else None

async def update_user_ban(user_id: int, ban_status: bool):
    """Админская функция: блокировка или разблокировка пользователя"""
    supabase.table("users").update({"is_banned": ban_status}).eq("user_id", user_id).execute()

async def activate_trial(user_id: int, end_date_str: str):
    """Активация бесплатного 3-дневного периода (с защитой от повтора)"""
    supabase.table("users").update({
        "subscription_end": end_date_str,
        "used_trial": True,
        "active_services": "combo"  # На тест выдаем максимальный пакет (Комбо)
    }).eq("user_id", user_id).execute()

async def add_subscription(user_id: int, end_date_str: str, service_type: str):
    """Обновление подписки в базе после успешной оплаты через Telegram Stars"""
    supabase.table("users").update({
        "subscription_end": end_date_str,
        "active_services": service_type
    }).eq("user_id", user_id).execute()

async def get_all_users():
    """Получение списка всех пользователей для админской рассылки"""
    res = supabase.table("users").select("user_id").execute()
    return [row["user_id"] for row in res.data] if res.data else []

async def get_promocode(code: str):
    """Поиск промокода в динамической таблице базы данных"""
    res = supabase.table("promocodes").select("*").eq("code", code).execute()
    return res.data[0] if res.data else None

async def decrease_promo_uses(code: str, current_uses: int):
    """Уменьшение счетчика оставшихся активаций промокода на 1"""
    supabase.table("promocodes").update({"uses": current_uses - 1}).eq("code", code).execute()

async def create_new_promocode(code: str, promo_type: str, value: int, uses: int):
    """Админская функция: создание нового промокода прямо из бота"""
    supabase.table("promocodes").insert({
        "code": code,
        "type": promo_type,
        "value": value,
        "uses": uses
    }).execute()
