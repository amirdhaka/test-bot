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
    return "Bot is alive!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_server).start()

# ---------- TOKEN ----------
TOKEN = "8773704187:AAGTsdTedZNUuBYaKsrNUHE1DLt7sjakHJg"

# ---------- CLEAN KEY ----------
def clean_key(text):
    return text.lower().replace("'", "").replace("’", "").strip()

# ---------- FORMAT KEY (DISPLAY FIX) ----------
def format_key(key):
    mapping = {
        "name": "Name",
        "fathers name": "Father's Name",
        "father name": "Father's Name",
        "mothers name": "Mother's Name",
        "mother name": "Mother's Name",
        "result": "Result",
        "institute": "Institute"
    }
    return mapping.get(key, key.title())

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

        info = {}

        # ✅ Extract all table data
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                key = clean_key(cols[0].text)
                val = cols[1].text.strip()
                info[key] = val

        # ✅ Get main fields
        name = info.get("name", "N/A")
        father = info.get("fathers name") or info.get("father name", "N/A")
        mother = info.get("mothers name") or info.get("mother name", "N/A")
        result_status = info.get("result", "N/A")
        institute = info.get("institute", "N/A")

        # ✅ Subjects
        subjects = ""
        skip_keys = [
            "name", "fathers name", "father name",
            "mothers name", "mother name",
            "result", "institute",
            "passing year", "center"
        ]

        for key, val in info.items():
            if key not in skip_keys:
                subjects += f"🔹 {format_key(key)} ➤ {val}\n"

        return name, father, mother, result_status, institute, subjects

    except Exception as e:
        print("Error:", e)
        return None

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🎓 Check HSC Result"]]
    await update.message.reply_text(
        "📢 Welcome!\nClick below 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ---------- HANDLE ----------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎓 Check HSC Result":
        await update.message.reply_text("🔢 Send Roll Number:")

    elif text.isdigit():
        await update.message.reply_text(f"⏳ Roll {text} এর রেজাল্ট খোঁজা হচ্ছে...")

        result = get_result(text)

        if not result:
            await update.message.reply_text("❌ Result not found / Server error")
            return

        name, father, mother, res_status, institute, subjects = result

        status_emoji = "❌ FAIL" if "fail" in res_status.lower() else "✅ PASSED"

        msg = f"""
✨ HSC RESULT 2025 (JASHORE)
━━━━━━━━━━━━━━━━━━

👨‍🎓 STUDENT INFO
👤 Name: {name}
👨 Father's Name: {father}
👩 Mother's Name: {mother}

📊 RESULT
🆔 Roll: {text}
📌 Status: {status_emoji}

🏫 {institute}

📚 SUBJECTS
━━━━━━━━━━━━━━━━━━
{subjects}
"""

        await update.message.reply_text(msg)

    else:
        await update.message.reply_text("❗ Click button and send roll number")

# ---------- RUN ----------
if __name__ == "__main__":
    keep_alive()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 BOT RUNNING...")
    app.run_polling()
