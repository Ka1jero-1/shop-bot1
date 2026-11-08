import telebot
from telebot import types
import os
from flask import Flask
from threading import Thread

# --- НАСТРОЙКИ ---
TOKEN = '9003569350:AAGJ27eWDJcncKYpG8dwDLvg2il9lC-ll1w' # Сюда вставь токен НОВОГО бота (не анонимного!)
ADMIN_ID = 5419168665 # Твой ID, чтобы заказы приходили тебе

# --- КАТАЛОГ ТОВАРОВ ---
# Можешь менять названия, цены и описания
CATALOG = {
    "item_1": {"name": "Футболка Oversize", "price": "150 000 сум", "desc": "Черная, 100% хлопок. Размеры S-XL."},
    "item_2": {"name": "Кружка 'Кодер'", "price": "80 000 сум", "desc": "Белая керамическая кружка с принтом."},
    "item_3": {"name": "Стикерпак", "price": "30 000 сум", "desc": "Набор из 10 виниловых стикеров."}
}

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Shop bot is working!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ИНИЦИАЛИЗАЦИЯ БОТА ---
bot = telebot.TeleBot(TOKEN)

# Хранилище данных пользователей во время оформления заказа
user_cart = {}

# --- ГЛАВНОЕ МЕНЮ ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_catalog = types.InlineKeyboardButton("🛒 Каталог", callback_data="show_catalog")
    btn_about = types.InlineKeyboardButton("ℹ️ О нас", callback_data="about")
    markup.add(btn_catalog, btn_about)
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 
                     f"Привет, {message.from_user.first_name}! Добро пожаловать в наш магазин.\nВыбери действие:", 
                     reply_markup=main_menu())

# --- ОБРАБОТКА КНОПОК ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "show_catalog":
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key, item in CATALOG.items():
            btn = types.InlineKeyboardButton(f"{item['name']} - {item['price']}", callback_data=f"view_{key}")
            markup.add(btn)
        btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")
        markup.add(btn_back)
        bot.edit_message_text("Выбери товар для подробностей:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("view_"):
        item_key = call.data.split("_")[1]
        item = CATALOG[item_key]
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_buy = types.InlineKeyboardButton("✅ Купить", callback_data=f"buy_{item_key}")
        btn_back = types.InlineKeyboardButton("⬅️ Назад в каталог", callback_data="show_catalog")
        markup.add(btn_buy, btn_back)
        
        text = f"*{item['name']}*\n\n{item['desc']}\n\n💰 Цена: *{item['price']}*"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)

    elif call.data.startswith("buy_"):
        item_key = call.data.split("_")[1]
        user_cart[call.from_user.id] = {"item": CATALOG[item_key]["name"], "price": CATALOG[item_key]["price"]}
        
        bot.send_message(call.message.chat.id, "Отлично! Давай оформим заказ.\n\nНапиши свое *Имя*:", parse_mode='Markdown')
        bot.register_next_step_handler(call.message, process_name_step)

    elif call.data == "back_to_menu":
        bot.edit_message_text("Главное меню:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    
    elif call.data == "about":
        bot.send_message(call.message.chat.id, "Мы лучший магазин в Telegram! Работаем 24/7.")
        bot.answer_callback_query(call.id)

# --- ОФОРМЛЕНИЕ ЗАКАЗА ---
def process_name_step(message):
    try:
        user_id = message.from_user.id
        user_cart[user_id]["name"] = message.text
        bot.send_message(message.chat.id, "Отлично. Теперь напиши свой *номер телефона* для связи:", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_phone_step)
    except Exception as e:
        bot.reply_to(message, "Что-то пошло не так. Попробуй еще раз через /start")

def process_phone_step(message):
    try:
        user_id = message.from_user.id
        user_cart[user_id]["phone"] = message.text
        order = user_cart[user_id]
        
        # Ответ клиенту
        bot.send_message(message.chat.id, "✅ Спасибо! Твой заказ принят. Мы свяжемся с тобой в ближайшее время.")
        
        # Отправка заказа тебе (Админу)
        admin_text = (f"🔥 *НОВЫЙ ЗАКАЗ!*\n\n"
                      f"Товар: {order['item']}\n"
                      f"Цена: {order['price']}\n"
                      f"Имя: {order['name']}\n"
                      f"Телефон: {order['phone']}\n"
                      f"Юзер: @{message.from_user.username}")
        bot.send_message(ADMIN_ID, admin_text, parse_mode='Markdown')
        
        # Очистка корзины
        del user_cart[user_id]
        
    except Exception as e:
        bot.reply_to(message, "Что-то пошло не так. Попробуй еще раз через /start")

# --- ЗАПУСК ---
if __name__ == "__main__":
    keep_alive()
    print("Бот-магазин запущен!")
    bot.polling(none_stop=True)
