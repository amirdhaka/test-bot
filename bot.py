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

        rows = soup.find_all("tr")

        name = father = mother = institute = result_status = "N/A"

        subjects = ""

        for row in rows:
            cols = row.find_all("td")

            if len(cols) == 2:
                key = cols[0].text.strip().lower()
                value = cols[1].text.strip()

                # Main info
                if key == "name":
                    name = value
                elif "father" in key:
                    father = value
                elif "mother" in key:
                    mother = value
                elif "institute" in key:
                    institute = value
                elif "result" in key:
                    result_status = value

                # Subjects filter
                elif key not in ["center", "passing year"]:
                    if len(value) <= 3:  # grade usually short
                        subjects += f"➡️ {cols[0].text.strip()} → {value}\n"

        return name, father, mother, result_status, institute, subjects

    except:
        return None

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🎓 Check HSC 2025 (Jashore)"]]
    await update.message.reply_text(
        "📢 Welcome!\nSelect option 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ---------- HANDLE ----------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎓 Check HSC 2025 (Jashore)":
        await update.message.reply_text("🔢 আপনার Roll Number দিন:")

    elif text.isdigit():
        roll = text
        await update.message.reply_text(f"⏳ রোল {roll} এর রেজাল্ট খোঁজা হচ্ছে...")

        result = get_result(roll)

        if not result:
            await update.message.reply_text("❌ Result not found / Server error")
            return

        name, father, mother, res_status, institute, subjects = result

        msg = f"""
🌟 HSC RESULT 2025 (JASHORE)
━━━━━━━━━━━━━━━━━━━━

👤 Name: {name}
👨 Father: {father}
👩 Mother: {mother}
🎂 DOB: {dob}

📘 RESULT {data['year']}
━━━━━━━━━━━━━━━
🆔 Roll: {data['roll']}
📄 Reg: {data['reg']}
🏫 Board: {data['board'].upper()}

📊 Result: {result_status}
⭐ GPA: {gpa}

🏫 {institute}

📚 Grade Sheet:
━━━━━━━━━━━━━━━━━━━━
{subjects}
"""

        await update.message.reply_text(msg)

    else:
        await update.message.reply_text("❗ বাটনে ক্লিক করে তারপর রোল নাম্বার দিন")

# ---------- RUN ----------
if __name__ == "__main__":
    keep_alive()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 BOT RUNNING SUCCESSFULLY")
    app.run_polling()
