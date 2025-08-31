import telebot
from telebot import types
import datetime
from flask import Flask
import threading
import os

# ==============================
# BOT CONFIG
# ==============================
TOKEN = os.getenv("BOT_TOKEN", "8186807833:AAHsc7cLR5K6zACzSkZUpcRP2C_Vq75rGy0")  # safer for Render secrets
OWNER_ID = 7301067810  # Replace with your Telegram ID

bot = telebot.TeleBot(TOKEN)

# Questions & answers
questions = [
    {
        "question": "🌱 What Plant Has A Candy Fruit?",
        "options": ["Candy Blossom", "Bone Blossom", "Carrot"],
        "answer": "Candy Blossom"
    },
    {
        "question": "🐙 What Pet Can Copy Other Pets' Ability?",
        "options": ["Dragon Fly", "Corrupted Kitsune", "Mimic Octopus"],
        "answer": "Mimic Octopus"
    }
]

# Server choices
servers = {
    "Update Announcements": "https://t.me/+FhZw-3u3cVtkZDVl",
    "Trading": "https://t.me/+HAy84jV_BEJmNmRl",
    "Buy & Sell": "https://t.me/+bu3d-sfXgakwN2Jl"
}

# Track user progress
user_data = {}

# ==============================
# BOT HANDLERS
# ==============================

@bot.message_handler(commands=["start"])
def start(message):
    user_data[message.chat.id] = {"step": 0, "attempts": 0, "answers": []}
    ask_question(message.chat.id)

def ask_question(chat_id):
    data = user_data[chat_id]
    step = data["step"]

    if step < len(questions):
        q = questions[step]
        markup = types.InlineKeyboardMarkup()
        for opt in q["options"]:
            markup.add(types.InlineKeyboardButton(opt, callback_data=f"answer|{opt}"))
        bot.send_message(chat_id, f"❓ {q['question']}", reply_markup=markup)
    else:
        choose_server(chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer"))
def handle_answer(call):
    chat_id = call.message.chat.id
    data = user_data.get(chat_id)

    if not data:
        return

    chosen = call.data.split("|")[1]
    step = data["step"]
    correct = questions[step]["answer"]

    if chosen == correct:
        data["answers"].append(f"Q{step+1}: ✅ Correct ({chosen})")
        data["step"] += 1
        ask_question(chat_id)
    else:
        data["attempts"] += 1
        data["answers"].append(f"Q{step+1}: ❌ Wrong ({chosen})")
        if data["attempts"] >= 3:
            bot.send_message(chat_id, "🚫 You answered wrong too many times. You are blocked.")
            bot.send_message(OWNER_ID, f"⚠️ User @{call.from_user.username} was blocked after 3 wrong attempts.")
            user_data.pop(chat_id, None)
        else:
            bot.send_message(chat_id, f"❌ Wrong! Try again ({3 - data['attempts']} attempts left)")
            ask_question(chat_id)

def choose_server(chat_id):
    markup = types.InlineKeyboardMarkup()
    for name in servers.keys():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"server|{name}"))
    bot.send_message(chat_id, "🎯 Congratulations! You passed the test.\n\nChoose which server you want to join:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("server"))
def handle_server(call):
    chat_id = call.message.chat.id
    data = user_data.get(chat_id)
    if not data:
        return

    server_name = call.data.split("|")[1]
    link = servers[server_name]

    bot.send_message(chat_id, f"✅ You chose **{server_name}**.\nHere is your invite link:\n{link}")

    # Prepare final report
    username = f"@{call.from_user.username}" if call.from_user.username else f"{call.from_user.first_name}"
    report = (
        "📋 Grow A Garden Recruiter Report\n\n"
        + "\n".join(data["answers"])
        + f"\n\n📌 Server Joined: {server_name}"
        + f"\n👤 Username: {username}"
        + f"\n📅 Date Joined: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    bot.send_message(OWNER_ID, report)

    # Clear data
    user_data.pop(chat_id, None)

# ==============================
# FLASK KEEP-ALIVE SERVER
# ==============================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot is running on Render!", 200

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ==============================
# RUN BOTH BOT + WEB
# ==============================
def run_bot():
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()