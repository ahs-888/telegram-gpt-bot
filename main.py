import telebot
from telebot import types
import openai
import os

# === НАСТРОЙКИ ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

# === Состояния ===
user_state = {}
user_free_uses = {}

AGENTS = {
    "presentations": """
Ты — экспертный AI-ассистент по созданию структурированных бизнес-презентаций в консалтинговом стиле.

🔍 Специализация:
- Работаешь по принципу пирамиды Минто (сначала вывод — потом аргументы)
- Используешь подходы McKinsey, BCG, Bain
- Применяешь инструменты: MECE, SWOT, 2x2, Roadmap, Dashboards и др.
- Подбираешь стиль и глубину под разную аудиторию: руководство, коллеги, клиенты, студенты

🧠 Ты умеешь:
- Помогать структурировать сложную идею в презентацию
- Создавать план, слайды и визуализацию
- Делать презентации логичными, убедительными и профессиональными

Перед созданием задаёшь уточняющие вопросы:
– Какова цель презентации?
– Кто целевая аудитория?
– Какие главные идеи ты хочешь донести?
– Какой желаемый объем (кол-во слайдов)?
– Какие методологии или стили ты предпочитаешь (если есть)?
"""
}

# === КОМАНДА /START ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_free_uses[message.chat.id] = 3
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📊 Презентации", callback_data="presentations"),
        types.InlineKeyboardButton("Промт под любую сферу", callback_data="any"),
        types.InlineKeyboardButton("Telegram пост", callback_data="tg"),
        types.InlineKeyboardButton("Маркетинг", callback_data="mkt"),
        types.InlineKeyboardButton("Копирайтинг", callback_data="copy"),
        types.InlineKeyboardButton("E-commerce", callback_data="ecom")
    )
    bot.send_message(message.chat.id, "👋 Привет! Выбери категорию ассистента:", reply_markup=markup)

# === ВЫБОР КНОПКИ ===
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_state[call.message.chat.id] = call.data
    bot.send_message(call.message.chat.id, "🧠 Напиши, для чего тебе нужен промт:")

# === ОБРАБОТКА ЗАПРОСА ===
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    if user_id not in user_state:
        return bot.send_message(user_id, "Сначала выбери категорию: /start")

    # Лимит бесплатного использования
    if user_free_uses.get(user_id, 0) <= 0:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔓 Купить доступ", url="https://your-payment-link.com"))
        return bot.send_message(user_id, "Вы использовали все 3 бесплатных промта. Чтобы продолжить — оплатите доступ:", reply_markup=markup)

    prompt = message.text
    category = user_state[user_id]

    if category == "presentations":
        system_message = AGENTS["presentations"]
    else:
        system_message = f"Ты ассистент категории {category}. Создай полезный промт по теме: {prompt}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # ← заменено с gpt-4 на стабильную версию
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        result = response['choices'][0]['message']['content']
    except Exception as e:
        return bot.send_message(user_id, f"❌ Ошибка при обращении к OpenAI:\n{e}")

    user_free_uses[user_id] -= 1
    bot.send_message(user_id, f"🔹 Готово!\n\n{result}\n\n✅ Осталось бесплатных генераций: {user_free_uses[user_id]} из 3")

# === ЗАПУСК ===
bot.polling(none_stop=True)
