import requests
import os
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------- KEEP ALIVE (Render/Replit) ----------
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ---------- TELEGRAM TOKEN ----------
TOKEN = "8773704187:AAGTsdTedZNUuBYaKsrNUHE1DLt7sjakHJg"

# ---------- RESULT FETCH FUNCTION ----------
def fetch_result(roll):
    url = "https://www.jessoreboard.gov.bd/resultjbh25/result.php"

    payload = {
        "roll": roll,
        "regno": ""
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        def get_value(label):
            tag = soup.find(string=label)
            return tag.find_next().text.strip() if tag else "N/A"

        name = get_value("Name")
        father = get_value("Father's Name")
        mother = get_value("Mother's Name")
        result = get_value("Result")
        institute = get_value("Institute")

        subjects = ""
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                subjects += f"{cols[0].text.strip()} → {cols[1].text.strip()}\n"

        return name, father, mother, result, institute, subjects

    except:
        return None

# ---------- START COMMAND ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🔍 Check Result"]]
    await update.message.reply_text(
        "📢 Welcome!\nClick below 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ---------- MESSAGE HANDLER ----------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "🔍 Check Result":
        await update.message.reply_text("🔢 Enter Roll Number:")

    elif text.isdigit():
        await update.message.reply_text("⏳ Checking result...")

        data = fetch_result(text)

        if not data:
            await update.message.reply_text("❌ Result not found / Server problem!")
            return

        name, father, mother, result, institute, subjects = data

        msg = f"""
👨‍🎓 STUDENT INFO
━━━━━━━━━━━━━━━
👤 Name: {name}
👨 Father: {father}
👩 Mother: {mother}

📘 RESULT 2025
━━━━━━━━━━━━━━━
🆔 Roll: {text}
📊 Result: {result}

🏫 {institute}

📊 SUBJECTS
━━━━━━━━━━━━━━━
{subjects}
"""

        await update.message.reply_text(msg)

    else:
        await update.message.reply_text("❗ Please click 'Check Result' and send roll number")

# ---------- MAIN ----------
if __name__ == "__main__":
    keep_alive()

    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 BOT STARTED SUCCESSFULLY")
    bot.run_polling()
