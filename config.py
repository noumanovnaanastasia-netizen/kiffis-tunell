# 🔒 Чистые ключи — прямое подключение
BOT_TOKEN = "8917018432:AAHomlpYmXG6S1w_m7qg9I3X3C6oZ8tK0eM"
ADMIN_ID = 7303801260
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_kToM1N0N1v"

# 🎨 Временные пустые заглушки для баннеров
PHOTO_MAIN_MENU = ""
PHOTO_TARIFFS = ""
PHOTO_INSTRUCTIONS = ""
PHOTO_PROMO = ""
PHOTO_SUPPORT = ""

# 📖 Временные пустые заглушки для статей
URL_AGREEMENT = ""
URL_INSTR_IOS = ""
URL_INSTR_ANDROID = ""

# 🕊 Временные пустые заглушки для пулов
URL_AVENCORES_VPN = ""
URL_AVENCORES_COMBO = ""
URL_IGARECK_WHITELIST = ""

# 📊 Тарифная сетка (она нужна, чтобы кнопки не выдавали ошибку)
TARIFFS = {
    "base": {
        "3_days": {1: 7, 2: 10, 3: 12, 4: 13, 5: 14},
        "1_month": {1: 30, 2: 42, 3: 51, 4: 57, 5: 60},
        "3_months": {1: 70, 2: 98, 3: 119, 4: 133, 5: 140}
    },
    "premium": {
        "3_days": {1: 10, 2: 14, 3: 17, 4: 19, 5: 20},
        "1_month": {1: 36, 2: 50, 3: 61, 4: 68, 5: 72},
        "3_months": {1: 80, 2: 112, 3: 136, 4: 152, 5: 160}
    }
}

# 🎟 Стартовый набор промокодов
PROMOCODES_STARTUP = {
    "KiffissTunnel202": {"type": "percent", "value": 20, "uses": 2}
}
