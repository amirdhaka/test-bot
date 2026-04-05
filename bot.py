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
def home(): return "Bot is Online!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_server).start()

# ---------- YOUR TEST TOKEN ----------
TOKEN = "8773704187:AAGTsdTedZNUuBYaKsrNUHE1DLt7sjakHJg"

# ---------- FINAL SCRAPING FUNCTION ----------
def get_result(roll):
    # আপনার স্ক্রিনশট অনুযায়ী সঠিক লিঙ্ক (index.php)
    url = "https://www.jessoreboard.gov.bd/resultjbh25/index.php"
    
    # ব্রাউজার যেভাবে ডাটা পাঠায় (GET মেথড ট্রাই করা হচ্ছে)
    params = {
        "roll": roll,
        "regno": ""
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.jessoreboard.gov.bd/resultjbh25/index.php"
    }

    try:
        # আমরা এখানে POST এবং GET দুইটাই হ্যান্ডেল করার চেষ্টা করছি
        res = requests.get(url, params=params, headers=headers, timeout=15)
        
        # যদি GET-এ কাজ না হয়, তবে POST ট্রাই করবে
        if "Name" not in res.text:
            res = requests.post(url, data=params, headers=headers, timeout=15)

        soup = BeautifulSoup(res.text, "html.parser")
        
        name = father = mother = institute = result_status = "N/A"
        subjects = ""

        # যশোর বোর্ডের নতুন ফরম্যাট অনুযায়ী ডাটা বের করা
        rows = soup.find_all("tr")
        found_any = False

        for row in rows:
            tds = row.find_all("td")
            if len(tds) >= 2:
                key = tds[0].get_text(strip=True)
                val = tds[1].get_text(strip=True)

                if key == "Name":
                    name = val
                    found_any = True
                elif "Father" in key:
                    father = val
                elif "Mother" in key:
                    mother = val
                elif "Institute" in key:
                    institute = val
                elif "Result" == key:
                    result_status = val
                
                # গ্রেড শিট (Subject, Grade)
                if len(tds) == 3 and any(char.isdigit() for char in key):
                    subjects += f"➡️ {val} → {tds[2].get_text(strip=True)}\n"

        if not found_any:
            return None

        return (name, father, mother, result_status, institute, subjects)

    except Exception as e:
        print(f"Error: {e}")
        return "Error"

# ---------- TELEGRAM HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🎓 Check HSC 2025 (Jashore)"]]
    await update.message.reply_text(
        "👋 স্বাগতম ভাই! রেজাল্ট চেক করতে নিচের বাটনে চাপ দিন।",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎓 Check HSC 2025 (Jashore)":
        await update.message.reply_text("🔢 আপনার রোল নম্বরটি দিন:")
    
    elif text.isdigit():
        roll = text
        status_msg = await update.message.reply_text(f"⏳ রোল {roll}-এর রেজাল্ট চেক করছি...")

        result = get_result(roll)

        if result == "Error":
            await status_msg.edit_text("⚠️ সার্ভার কানেকশন এরর! আবার চেষ্টা করুন।")
        elif result is None:
            await status_msg.edit_text("❌ এই রোলের কোনো রেজাল্ট পাওয়া যায়নি।")
        else:
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
{sub_list if sub_list else "গ্রেড শিট লোড হয়নি"}
"""
            await status_msg.edit_text(msg, parse_mode='Markdown')

if __name__ == "__main__":
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("🚀 BOT IS RUNNING SUCCESSFULLY!")
    app.run_polling()
