import requests
import os
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------- KEEP ALIVE (For Deployment) ----------
server = Flask(__name__)

@server.route('/')
def home():
    return "Bot is Running!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_server).start()

# ---------- YOUR TEST TOKEN ----------
TOKEN = "8773704187:AAGTsdTedZNUuBYaKsrNUHE1DLt7sjakHJg"

# ---------- SCRAPING FUNCTION ----------
def get_result(roll):
    url = "https://www.jessoreboard.gov.bd/resultjbh25/result.php"
    data = {"roll": roll, "regno": ""}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        res = requests.post(url, data=data, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        rows = soup.find_all("tr")
        
        name = father = mother = institute = result_status = "N/A"
        subjects = ""

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)

                # সাইটের টেক্সট অনুযায়ী ম্যাচিং
                if "Name" == key:
                    name = value
                elif "Father" in key:
                    father = value
                elif "Mother" in key:
                    mother = value
                elif "Institute" in key:
                    institute = value
                elif "Result" == key:
                    result_status = value
                
                # গ্রেড শিট বের করার লজিক (কোড এবং গ্রেড ৩টি কলামে থাকলে)
                if len(cols) == 3:
                    grade = cols[2].get_text(strip=True)
                    # যদি কী কলামে কোনো সংখ্যা (Subject Code) থাকে
                    if any(char.isdigit() for char in key):
                        subjects += f"➡️ {value} → {grade}\n"

        return name, father, mother, result_status, institute, subjects
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

# ---------- TELEGRAM HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🎓 Check HSC 2025 (Jashore)"]]
    await update.message.reply_text(
        "👋 স্বাগতম! যশোর বোর্ডের রেজাল্ট দেখতে নিচের বাটনে ক্লিক করুন।",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎓 Check HSC 2025 (Jashore)":
        await update.message.reply_text("🔢 আপনার রোল নম্বরটি (Roll) লিখুন:")
    
    elif text.isdigit():
        roll = text
        status_msg = await update.message.reply_text(f"⏳ রোল {roll}-এর রেজাল্ট খোঁজা হচ্ছে... দয়া করে অপেক্ষা করুন।")

        result = get_result(roll)

        if not result or (result[0] == "N/A" and result[4] == "N/A"):
            await status_msg.edit_text("❌ রেজাল্ট পাওয়া যায়নি! রোল নম্বরটি চেক করে আবার চেষ্টা করুন।")
            return

        name, father, mother, res_status, inst, sub_list = result

        msg = f"""
🌟 *HSC RESULT 2025 (JASHORE)*
━━━━━━━━━━━━━━━━━━━━

👤 *Name:* {name}
👨 *Father:* {father}
👩 *Mother:* {mother}

🆔 *Roll:* {roll}
📊 *Status:* {res_status}

🏫 *Institute:* {inst}

📚 *Grade Sheet:*
━━━━━━━━━━━━━━━━━━━━
{sub_list if sub_list else "গ্রেড শিট পাওয়া যায়নি"}
"""
        await status_msg.edit_text(msg, parse_mode='Markdown')

    else:
        await update.message.reply_text("❗ অনুগ্রহ করে সঠিক রোল নম্বর দিন।")

# ---------- MAIN EXECUTION ----------
if __name__ == "__main__":
    # সার্ভার চালু রাখা (Render/Replit এর জন্য)
    keep_alive()

    # বট চালু করা
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("✅ BOT IS ONLINE NOW!")
    app.run_polling()
