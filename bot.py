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
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.jessoreboard.gov.bd/resultjbh25/index.php",
        "Origin": "https://www.jessoreboard.gov.bd",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    session.headers.update(headers)

    try:
        # Step 1: Load homepage (important)
        session.get("https://www.jessoreboard.gov.bd/resultjbh25/index.php")

        # Step 2: Send request
        res = session.post(
            "https://www.jessoreboard.gov.bd/resultjbh25/result.php",
            data={"roll": roll, "regno": ""}
        )

        # ❌ যদি valid result না আসে
        if "Roll No" not in res.text:
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        rows = soup.find_all("tr")

        info = {}
        subjects = ""

        for row in rows:
            cols = row.find_all("td")

            # Info table
            if len(cols) == 2:
                key = cols[0].text.strip()
                value = cols[1].text.strip()
                info[key] = value

            # Subject table
            elif len(cols) == 3:
                code = cols[0].text.strip()
                subject = cols[1].text.strip()
                grade = cols[2].text.strip()

                subjects += f"➡️ {code} → {subject} → {grade}\n"

        return info, subjects

    except Exception as e:
        print("Error:", e)
        return None

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🎓 Check HSC 2025 (Jashore)"]]
    await update.message.reply_text(
        "📢 Welcome!\nClick button 👇",
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
            await update.message.reply_text("❌ এই রোলের কোনো রেজাল্ট পাওয়া যায়নি")
            return

        info, subjects = result

        msg = f"""
🌟 HSC RESULT 2025 (JASHORE)
━━━━━━━━━━━━━━━━━━━━

👤 Name: {info.get('Name','N/A')}
👨 Father: {info.get("Father's Name",'N/A')}
👩 Mother: {info.get("Mother's Name",'N/A')}

🆔 Roll: {info.get('Roll No','N/A')}
📄 Reg: {info.get('Reg. No','N/A')}
📚 Group: {info.get('Group','N/A')}
📅 Session: {info.get('Session','N/A')}
📆 Year: {info.get('Passing Year','N/A')}
📌 Type: {info.get('Type','N/A')}

📊 Result: {info.get('Result','N/A')}
🏫 Institute: {info.get('Institute','N/A')}
📍 Center: {info.get('Center','N/A')}

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
