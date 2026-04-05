import requests
import os
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------- KEEP ALIVE ----------
server = Flask(__name__)

@server.route('/')
def home():
    return "I am alive!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_server).start()

# ---------- TOKEN ----------
TOKEN = "8773704187:AAGTsdTedZNUuBYaKsrNUHE1DLt7sjakHJg"

# ---------- RESULT FUNCTION ----------
def get_result(roll):
    url = "https://www.jessoreboard.gov.bd/resultjbh25/result.php"

    data = {
        "roll": roll,
        "regno": ""
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.post(url, data=data, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        def get_val(label):
            tag = soup.find(string=label)
            return tag.find_next().text.strip() if tag else "N/A"

        name = get_val("Name")
        father = get_val("Father's Name")
        mother = get_val("Mother's Name")
        result_status = get_val("Result")
        institute = get_val("Institute")

        subjects = ""
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                subjects += f"{cols[0].text.strip()} → {cols[1].text.strip()}\n"

        return name, father, mother, result_status, institute, subjects

    except:
        return None

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🔍 Check Result"]]
    await update.message.reply_text(
        "📢 Welcome!\nClick below 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ---------- HANDLE ----------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🔍 Check Result":
        await update.message.reply_text("🔢 Send Roll Number:")

    elif text.isdigit():
        await update.message.reply_text("⏳ Checking...")

        result = get_result(text)

        if not result:
            await update.message.reply_text("❌ Result not found / Server error")
            return

        name, father, mother, res_status, institute, subjects = result

        msg = f"""
👨‍🎓 STUDENT INFO
━━━━━━━━━━━━━━━
👤 Name: {name}
👨 Father: {father}
👩 Mother: {mother}

📘 RESULT 2025
━━━━━━━━━━━━━━━
🆔 Roll: {text}
📊 Result: {res_status}

🏫 {institute}

📊 SUBJECTS
━━━━━━━━━━━━━━━
{subjects}
"""

        await update.message.reply_text(msg)

    else:
        await update.message.reply_text("❗ Click 'Check Result' and send roll number")

# ---------- RUN ----------
if __name__ == "__main__":
    keep_alive()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 BOT RUNNING...")
    app.run_polling()
