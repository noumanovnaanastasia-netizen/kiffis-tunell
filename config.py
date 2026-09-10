import os

# 🔒 Переменные окружения (настраиваются в панели управления Render)
BOT_TOKEN = os.environ.get("8917018432:AAHomlpYmYcmM_-KMv0TsrmQ_Xv4xBFfDjc")
ADMIN_ID = int(os.environ.get("7303801260", 0))
SUPABASE_URL = os.environ.get("https://ftefxgzjhzokapqokprd.supabase.com")
SUPABASE_KEY = os.environ.get("sb_publishable_kTrpcThrV4nzfruaADpQ7w_TSpFTlFW")

# 🎨 Ссылки на твои потрясающие баннеры из канала @banerss777
PHOTO_MAIN_MENU = "https://t.me/banerss777/9"
PHOTO_TARIFFS = "https://t.me/banerss777/8"
PHOTO_INSTRUCTIONS = "https://t.me/banerss777/7"
PHOTO_PROMO = "https://t.me/banerss777/6"
PHOTO_SUPPORT = "https://t.me/banerss777/11"

# 📖 Официальные ссылки на твои статьи в Telegra.ph
URL_AGREEMENT = "https://telegra.ph/Polzovatelskoe-soglashenie-i-Politika-konfidencialnosti-Kiffis-Tunnel-09-10"
URL_INSTR_IOS = "https://telegra.ph/Podrobnaya-instrukciya-dlya-iOS-iPhone--iPad-09-10"
URL_INSTR_ANDROID = "https://telegra.ph/Podrobnaya-instrukciya-dlya-Android-09-10"

# 🕊 Текстовые ссылки на бесплатные пулы из проверенных репозиториев
URL_AVENCORES_VPN = "https://github.com/AvenCores/goida-vpn-configs"
URL_AVENCORES_COMBO = "https://githubusercontent.com"
URL_IGARECK_WHITELIST = "https://github.com/igareck/vpn-configs-for-russia"

# 📊 Утвержденная тарифная сетка в Telegram Stars (⭐)
# Сроки: 3_days, 1_month, 3_months. (Срок 14_days будет считаться кодом автоматически)
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

# 🎟 Стартовый набор твоих авторских промокодов для первой заливки в базу данных Supabase
PROMOCODES_STARTUP = {
    "KiffissTunnel202": {"type": "percent", "value": 20, "uses": 2},
    "Gissitor": {"type": "stars", "value": 5, "uses": 2},
    "Hoprtt": {"type": "stars", "value": 10, "uses": 2},
    "BeSpLaTnO": {"type": "bonus_days", "value": 2, "uses": 3},      # 2 дня бесплатного комбо
    "LbgoTa": {"type": "bonus_days", "value": 3, "uses": 1},         # 3 дня белых списков
    "SakeraHarena": {"type": "bonus_days", "value": 5, "uses": 3},    # 5 дней белых списков
    "QhcpTTlo": {"type": "percent_condition", "value": 40, "uses": 5} # -40% если цена от 50 звезд
}
