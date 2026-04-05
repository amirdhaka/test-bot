import requests
import os
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------- FLASK SETUP ----------
server = Flask(__name__)

@server.route('/')
def home():
    return "Jashore Board Bot is Running!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()
# ---------------------------------

# আপনার দেওয়া টেস্ট টোকেন
TOKEN = "8773704187:AAGTsdTedZNUuBYaKsrNUHE1DLt7sjakHJg"

# ---------- JASHORE BOARD RESULT FETCH ----------
def get_jashore_result(roll):
    url = "https://www.jessoreboard.gov.bd/resultjbh25/result.php"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": "https://www.jessoreboard.gov.bd/resultjbh25/index.php",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # শুধু রোল পাঠানো হচ্ছে, রেজিস্ট্রেশন নম্বর ফাঁকা রাখা হয়েছে
    payload = {
        "roll": roll,
        "regno": "" 
    }

    try:
        session = requests.Session()
        response = session.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🎓 Check HSC 2025 (Jashore)"]]
    await update.message.reply_text(
        "👋 আসসালামু আলাইকুম!\nযশোর বোর্ডের রেজাল্ট দেখতে নিচের বাটনে ক্লিক করুন।",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ---------- HANDLE MESSAGE ----------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text

    # স্টেট সেভ করার জন্য context.user_data ব্যবহার করছি
    if text == "🎓 Check HSC 2025 (Jashore)":
        context.user_data['waiting_for_roll'] = True
        await update.message.reply_text("🔢 আপনার **Roll Number** টি দিন:")

    elif context.user_data.get('waiting_for_roll'):
        if text.isdigit():
            roll = text
            await update.message.reply_text(f"⏳ রোল {roll}-এর রেজাল্ট খোঁজা হচ্ছে...")

            html = get_jashore_result(roll)

            if not html or "Result not found" in html or "Invalid" in html:
                await update.message.reply_text("❌ রেজাল্ট পাওয়া যায়নি! সঠিক রোল নম্বর দিন।")
            else:
                soup = BeautifulSoup(html, "html.parser")
                try:
                    # তথ্য স্ক্র্যাপ করা
                    all_tds = soup.find_all('td')
                    info = {}
                    for i in range(len(all_tds)):
                        txt = all_tds[i].get_text().strip()
                        if "Name" in txt and ":" not in txt:
                            info['Name'] = all_tds[i+1].get_text().strip()
                        elif "Father's Name" in txt:
                            info['Father'] = all_tds[i+1].get_text().strip()
                        elif "Result" in txt and i+1 < len(all_tds):
                            info['Status'] = all_tds[i+1].get_text().strip()

                    # সাবজেক্ট গ্রেড
                    subject_list = ""
                    rows = soup.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            grade = cols[-1].get_text().strip()
                            if grade in ['A+', 'A', 'A-', 'B', 'C', 'D', 'F']:
                                subject_list += f"🔹 {cols[0].get_text().strip()} ➔ **{grade}**\n"

                    result_msg = f"""
🌟 **HSC RESULT 2025 (JASHORE)** 🌟
━━━━━━━━━━━━━━━━━━
👤 **Name:** {info.get('Name', 'N/A')}
👨 **Father:** {info.get('Father', 'N/A')}
🆔 **Roll:** {roll}
📊 **Status:** {info.get('Status', 'N/A')}
━━━━━━━━━━━━━━━━━━
📚 **Grade Sheet:**
{subject_list if subject_list else "গ্রেড পাওয়া যায়নি।"}
━━━━━━━━━━━━━━━━━━
"""
                    await update.message.reply_text(result_msg, parse_mode='Markdown')
                except:
                    await update.message.reply_text("⚠️ ডাটা প্রসেস করতে সমস্যা হয়েছে।")
            
            context.user_data['waiting_for_roll'] = False
        else:
            await update.message.reply_text("❌ দয়া করে শুধু সংখ্যায় রোল নম্বর দিন।")

# ---------- RUN ----------
if __name__ == "__main__":
    keep_alive()
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("🚀 BOT IS LIVE WITH ROLL-ONLY MODE! ✅")
    bot_app.run_polling()
