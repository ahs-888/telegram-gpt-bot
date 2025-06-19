import telebot
from telebot import types
import openai
import os

# === НАСТРОЙКИ ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

# Словарь для хранения состояния пользователя
user_state = {}
user_free_uses = {}

# === ХЕНДЛЕР СТАРТА ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_free_uses[message.chat.id] = 3  # даём 3 бесплатных генерации
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Промт под любую сферу", callback_data="any"),
        types.InlineKeyboardButton("Telegram пост", callback_data="tg"),
        types.InlineKeyboardButton("Маркетинг", callback_data="mkt"),
        types.InlineKeyboardButton("Копирайтинг", callback_data="copy"),
        types.InlineKeyboardButton("E-commerce", callback_data="ecom")
    )
    bot.send_message(message.chat.id, "👋 Привет! Выбери категорию ассистента:", reply_markup=markup)

# === ОБРАБОТКА КНОПОК ===
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_state[call.message.chat.id] = call.data
    bot.send_message(call.message.chat.id, "🧠 Напиши, для чего тебе нужен промт:")

# === ОБРАБОТКА СООБЩЕНИЙ ===
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    if user_id not in user_state:
        return bot.send_message(user_id, "Сначала выбери категорию: /start")

    # Проверка бесплатных использований
    if user_free_uses.get(user_id, 0) <= 0:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔓 Купить доступ", url="https://your-payment-link.com"))
        return bot.send_message(user_id, "Вы использовали все 3 бесплатных промта. Чтобы продолжить — оплатите доступ:", reply_markup=markup)

    prompt = message.text
    category = user_state[user_id]
    full_prompt = f"Ты ассистент категории {category}. Создай полезный промт по теме: {prompt}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": full_prompt}]
        )
        result = response['choices'][0]['message']['content']
    except Exception as e:
        return bot.send_message(user_id, f"Ошибка при обращении к OpenAI: {e}")

    user_free_uses[user_id] -= 1
    bot.send_message(user_id, f"🔹 Готово!\n\n{result}\n\n✅ Осталось бесплатных генераций: {user_free_uses[user_id]} из 3")

# === ЗАПУСК ===
bot.polling(none_stop=True)
