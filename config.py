import os

# 🔒 Переменные окружения (подключаются в настройках Render)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 🎨 Ссылки на твои потрясающие баннеры с Telegra.ph
PHOTO_MAIN_MENU = "https://telegra.ph"
PHOTO_TARIFFS = "https://telegra.ph"
PHOTO_INSTRUCTIONS = "https://telegra.ph"
PHOTO_PROMO = "https://telegra.ph"

# 🕊 Текстовые ссылки на бесплатные пулы из проверенных репозиториев
URL_AVENCORES_VPN = "https://github.com"
URL_AVENCORES_COMBO = "https://github.com"
URL_IGARECK_WHITELIST = "https://github.com"

# 📊 Утвержденная тарифная сетка в Telegram Stars (⭐)
TARIFFS = {
    "base": {  # Настоящие Прокси и обычный VPN
        "3_days": {1: 7, 2: 10, 3: 12, 4: 13, 5: 14},
        "1_month": {1: 30, 2: 42, 3: 51, 4: 57, 5: 60},
        "3_months": {1: 70, 2: 98, 3: 119, 4: 133, 5: 140}
    },
    "premium": {  # Белые списки и Комбо (Всё вместе)
        "3_days": {1: 10, 2: 14, 3: 17, 4: 19, 5: 20},
        "1_month": {1: 36, 2: 50, 3: 61, 4: 68, 5: 72},
        "3_months": {1: 80, 2: 112, 3: 136, 4: 152, 5: 160}
    }
}

# 🎟 Стартовый набор твоих авторских промокодов со скидками и бонусами
PROMOCODES_STARTUP = {
    "KiffissTunnel202": {"type": "percent", "value": 20, "uses": 2},
    "Gissitor": {"type": "stars", "value": 5, "uses": 2},
    "Hoprtt": {"type": "stars", "value": 10, "uses": 2},
    "BeSpLaTnO": {"type": "bonus_days", "value": 2, "uses": 3},   # 2 дня бесплатного комбо
    "LbgoTa": {"type": "bonus_days", "value": 3, "uses": 1},       # 3 дня белых списков
    "SakeraHarena": {"type": "bonus_days", "value": 5, "uses": 3}, # 5 дней белых списков
    "QhcpTTlo": {"type": "percent_condition", "value": 40, "uses": 5} # -40% если цена от 50 звезд
}
