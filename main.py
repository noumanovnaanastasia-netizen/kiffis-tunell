import os
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telebot import TeleBot, types

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)

URL_MAIN_IMG = "https://placehold.co"

# Ссылки на твои статьи в Telegraph
URL_IOS = "https://telegra.ph/Podrobnaya-instrukciya-dlya-iOS-iPhone--iPad-09-10"
URL_ANDROID = "https://telegra.ph/Podrobnaya-instrukciya-dlya-Android-09-10"
URL_AGREE = "https://telegra.ph/Polzovatelskoe-soglashenie-i-Politika-konfidencialnosti-Kiffis-Tunnel-09-10"


# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Kiffis Tunnel работает!".encode("utf-8"))

def run_web_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), WebServer)
    logging.info(f"Веб-сервер запущен на порту {port}")
    server.serve_forever()


# --- ГЛАВНОЕ МЕНЮ ---
@bot.message_handler(commands=['start'])
def cmd_start(message):
    markup = types.InlineKeyboardMarkup()
    
    btn_vpn = types.InlineKeyboardButton("🌐 Просто VPN", callback_data="menu_vpn")
    btn_proxy = types.InlineKeyboardButton("🧦 Прокси", callback_data="menu_proxy")
    markup.row(btn_vpn, btn_proxy)
    
    btn_wl = types.InlineKeyboardButton("🤍 Белые списки", callback_data="menu_wl")
    btn_combo = types.InlineKeyboardButton("🔄 VPN + БС (Комбо)", callback_data="menu_combo")
    markup.row(btn_wl, btn_combo)
    
    btn_ins = types.InlineKeyboardButton("📖 Инструкция", callback_data="sub_menu_instruction") 
    btn_promo = types.InlineKeyboardButton("🎟 Промокоды", callback_data="menu_promo")
    markup.row(btn_ins, btn_promo)
    
    btn_help = types.InlineKeyboardButton("🆘 Помощь", callback_data="menu_help")
    btn_agree = types.InlineKeyboardButton("📄 Соглашение", url=URL_AGREE)
    markup.row(btn_help, btn_agree)
    
    bot.send_photo(
        message.chat.id,
        photo=URL_MAIN_IMG,
        caption=f"🔮 **Привет, {message.from_user.first_name}!**\n\nДобро пожаловать в туннель *Kiffis Tunnel*.\nВыбери необходимую услугу в меню ниже 👇",
        reply_markup=markup,
        parse_mode="Markdown"
    )


# --- CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data == "sub_menu_instruction":
        ins_markup = types.InlineKeyboardMarkup()
        btn_ios = types.InlineKeyboardButton("🍏 Инструкция для iOS", url=URL_IOS)
        btn_and = types.InlineKeyboardButton("🤖 Инструкция для Android", url=URL_ANDROID)
        btn_back = types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_to_main")
        ins_markup.row(btn_ios)
        ins_markup.row(btn_and)
        ins_markup.row(btn_back)
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="📱 **Выбери операционную систему твоего устройства:**",
            reply_markup=ins_markup,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id)
        
    elif call.data == "back_to_main":
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🌐 Просто VPN", callback_data="menu_vpn"), types.InlineKeyboardButton("🧦 Прокси", callback_data="menu_proxy"))
        markup.row(types.InlineKeyboardButton("🤍 Белые списки", callback_data="menu_wl"), types.InlineKeyboardButton("🔄 VPN + БС (Комбо)", callback_data="menu_combo"))
        markup.row(types.InlineKeyboardButton("📖 Инструкция", callback_data="sub_menu_instruction"), types.InlineKeyboardButton("🎟 Промокоды", callback_data="menu_promo"))
        markup.row(types.InlineKeyboardButton("🆘 Помощь", callback_data="menu_help"), types.InlineKeyboardButton("📄 Соглашение", url=URL_AGREE))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"🔮 **Привет!**\n\nДобро пожаловать в туннель *Kiffis Tunnel*.\nВыбери необходимую услугу в меню ниже 👇",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, text="Эта функция в разработке 🛠")


if __name__ == "__main__":
    # 1. Запуск веб-сервера
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # 2. Очистка старых зависших соединений в Telegram перед стартом
    logging.info("Сброс старых сессий Telegram...")
    try:
        bot.remove_webhook()
    except Exception as e:
        logging.warning(f"Не удалось удалить вебхук: {e}")
        
    time.sleep(2) # Небольшая пауза для стабилизации сессии
    
    logging.info("Бот Kiffis Tunnel успешно запущен...")
    
    # 3. Безопасный запуск опроса (игнорирует временные ошибки конфликта)
    bot.infinity_polling(skip_pending=True)
