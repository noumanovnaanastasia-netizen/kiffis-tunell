import asyncio
from datetime import datetime, timedelta
from supabase import create_client, Client
import config

# 🔌 Подключаемся к Supabase
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# 🧙‍♂️ Авто-создание всех таблиц прямо из кода
async def init_database():
    """Создает необходимые таблицы в Supabase через RPC exec_sql"""
    queries = [
        """
        CREATE TABLE IF NOT EXISTS public.users (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            expire_date TIMESTAMPTZ,
            tariff_type TEXT,
            devices INT DEFAULT 1,
            test_used BOOLEAN DEFAULT false,
            active_discount INT DEFAULT 0,
            active_minus_stars INT DEFAULT 0
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS public.promocodes (
            id BIGSERIAL PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            value INT NOT NULL,
            max_activations INT NOT NULL,
            current_activations INT DEFAULT 0
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS public.my_proxies (
            id BIGSERIAL PRIMARY KEY,
            proxy_link TEXT UNIQUE NOT NULL,
            assigned_to BIGINT REFERENCES public.users(user_id) ON DELETE SET NULL
        );
        """
    ]
    
    for query in queries:
        try:
            supabase.rpc("exec_sql", {"query": query}).execute()
        except Exception:
            pass

# 👤 ЛОГИКА ПОЛЬЗОВАТЕЛЕЙ
async def get_user(user_id: int):
    """Получает данные пользователя, учитывая особенности структуры ответа"""
    response = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if response.data:
        return response.data[0] if isinstance(response.data, list) else response.data
    return None

async def create_user(user_id: int, username: str):
    """Автоматически регистрирует нового пользователя"""
    user = await get_user(user_id)
    if not user:
        data = {
            "user_id": user_id,
            "username": username,
            "expire_date": None,
            "tariff_type": None,
            "devices": 1,
            "test_used": False
        }
        supabase.table("users").insert(data).execute()

async def activate_test_period(user_id: int):
    """Активирует бесплатный тест на 3 дня"""
    expire_at = datetime.now() + timedelta(days=3)
    supabase.table("users").update({
        "expire_date": expire_at.isoformat(),
        "tariff_type": "combo",
        "test_used": True
    }).eq("user_id", user_id).execute()

# 📊 СТАТИСТИКА ДЛЯ АДМИН-ПАНЕЛИ
async def get_admin_stats():
    """Собирает живую статистику из базы данных"""
    now = datetime.now().isoformat()
    
    all_users = supabase.table("users").select("user_id", count="exact").execute().count
    active_users = supabase.table("users").select("user_id", count="exact").gt("expire_date", now).execute().count
    test_users = supabase.table("users").select("user_id", count="exact").eq("test_used", True).execute().count
    
    vpn_cnt = supabase.table("users").select("user_id", count="exact").gt("expire_date", now).eq("tariff_type", "vpn").execute().count
    proxy_cnt = supabase.table("users").select("user_id", count="exact").gt("expire_date", now).eq("tariff_type", "proxy").execute().count
    whitelist_cnt = supabase.table("users").select("user_id", count="exact").gt("expire_date", now).eq("tariff_type", "whitelist").execute().count
    combo_cnt = supabase.table("users").select("user_id", count="exact").gt("expire_date", now).eq("tariff_type", "combo").execute().count
    
    return {
        "all": all_users or 0,
        "active": active_users or 0,
        "test": test_users or 0,
        "vpn": vpn_cnt or 0,
        "proxy": proxy_cnt or 0,
        "whitelist": whitelist_cnt or 0,
        "combo": combo_cnt or 0
    }

# 🎟 ЛОГИКА ПРОМОКОДОВ
async def apply_promo(user_id: int, code_text: str) -> str:
    """Активирует промокод и обрабатывает его типы без конфликтов кавычек"""
    promo_resp = supabase.table("promocodes").select("*").eq("code", code_text).execute()
    
    if not promo_resp.data:
        if code_text in config.PROMOCODES_STARTUP:
            p = config.PROMOCODES_STARTUP[code_text]
            supabase.table("promocodes").insert({
                "code": code_text, "type": p["type"], "value": p["value"], "max_activations": p["uses"]
            }).execute()
            promo_resp = supabase.table("promocodes").select("*").eq("code", code_text).execute()
        else:
            return "❌ Такого промокода не существует, котик."

    promo_data = promo_resp.data
    promo = promo_data[0] if isinstance(promo_data, list) else promo_data
    
    if promo["current_activations"] >= promo["max_activations"]:
        return "❌ К сожалению, этот промокод уже полностью разобрали!"

    p_type = promo["type"]
    p_val = promo["value"]

    if p_type == "percent":
        supabase.table("users").update({"active_discount": p_val}).eq("user_id", user_id).execute()
        res = f"🎟 Промокод применен! Твоя скидка {p_val}% на следующую покупку."
    elif p_type == "stars":
        supabase.table("users").update({"active_minus_stars": p_val}).eq("user_id", user_id).execute()
        res = f"🎟 Промокод применен! Ты получишь скидку в {p_val} ⭐ Stars."
    elif p_type == "bonus_days":
        user = await get_user(user_id)
        current_expire = datetime.fromisoformat(user["expire_date"]) if (user and user.get("expire_date")) else datetime.now()
        new_expire = max(current_expire, datetime.now()) + timedelta(days=p_val)
        supabase.table("users").update({
            "expire_date": new_expire.isoformat(),
            "tariff_type": "combo"
        }).eq("user_id", user_id).execute()
        res = f"🎁 Ура! Тебе начислено +{p_val} дней бесплатной подписки!"
    elif p_type == "percent_condition":
        supabase.table("users").update({"active_discount": p_val}).eq("user_id", user_id).execute()
        res = f"🎟 Промокод применен! Скидка {p_val}% сработает на тарифы от 50 звезд."
    else:
        return "❌ Ошибка активации кода."

    supabase.table("promocodes").update({"current_activations": promo["current_activations"] + 1}).eq("code", code_text).execute()
    return res

# 🧦 ЛОГИКА ТВОИХ ЛИЧНЫХ ПРОКСИ
async def assign_free_proxy(user_id: int) -> str:
    """Берет один свободный прокси со склада и привязывает к пользователю"""
    response = supabase.table("my_proxies").select("*").is_("assigned_to", "null").limit(1).execute()
    if response.data:
        proxy_data = response.data
        proxy = proxy_data[0] if isinstance(proxy_data, list) else proxy_data
        # Баг исправлен: привязываем через правильный proxy["id"]
        supabase.table("my_proxies").update({"assigned_to": user_id}).eq("id", proxy["id"]).execute()
        return proxy["proxy_link"]
    return "⚠️ Наши приватные прокси временно закончились! Напиши в [🆘 Поддержка], администратор сразу добавит новые."
