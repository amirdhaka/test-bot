import requests
import os
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------- FLASK SETUP (For Render/Replit) ----------
server = Flask(__name__)

@server.route('/')
def home():
    return "Jashore Board Bot is Alive and Running!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()
# -----------------------------------------------------

# আপনার দেওয়া টেস্ট এপিআই টোকেন
TOKEN = "8773704187:AAGTsdTedZNUuBYaKsrNUHE1DLt7sjakHJg"

user_data = {}

# ---------- JASHORE BOARD RESULT FETCH ----------
def get_jashore_result(roll, regno):
    url = "https://www.jessoreboard.gov.bd/resultjbh25/result.php"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": "https://www.jessoreboard.gov.bd/resultjbh25/index.php",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    payload = {
        "roll": roll,
        "regno": regno
    }

    try:
        session = requests.Session()
        response = session.post(url, data=payload, headers=headers)
        
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# ---------- START COMMAND ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🎓 Check HSC 2025 (Jashore)"]]
    await update.message.reply_text(
        "👋 আসসালামু আলাইকুম!\nযশোর বোর্ডের ২০২৫ সালের এইচএসসি রেজাল্ট চেক করার টেস্ট বটে স্বাগতম।",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ---------- MESSAGE HANDLER ----------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text

    if chat_id not in user_data:
        user_data[chat_id] = {}

    data = user_data[chat_id]

    if text == "🎓 Check HSC 2025 (Jashore)":
        data.clear()
        data['step'] = 'get_roll'
        await update.message.reply_text("🔢 আপনার **Roll Number** টি লিখুন:")

    elif data.get('step') == 'get_roll':
        if text.isdigit():
            data['roll'] = text
            data['step'] = 'get_reg'
            await update.message.reply_text("📝 এবার আপনার **Registration Number** টি লিখুন:")
        else:
            await update.message.reply_text("❌ দয়া করে সঠিক রোল নম্বর (শুধু সংখ্যা) দিন।")

    elif data.get('step') == 'get_reg':
        data['reg'] = text
        await update.message.reply_text("⏳ রেজাল্ট সার্ভার থেকে খোঁজা হচ্ছে... একটু অপেক্ষা করুন।")

        html = get_jashore_result(data['roll'], data['reg'])

        if not html or "Result not found" in html:
            await update.message.reply_text("❌ রেজাল্ট পাওয়া যায়নি! রোল বা রেজিস্ট্রেশন নম্বর ভুল হতে পারে।")
            data.clear()
            return

        soup = BeautifulSoup(html, "html.parser")
        
        try:
            # ছাত্র-ছাত্রীর বেসিক তথ্য সংগ্রহ
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

            # গ্রেড শীট তৈরি
            subject_list = ""
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    sub_name = cols[0].get_text().strip()
                    grade = cols[-1].get_text().strip()
                    if grade in ['A+', 'A', 'A-', 'B', 'C', 'D', 'F']:
                        subject_list += f"🔹 {sub_name} ➔ **{grade}**\n"

            result_summary = f"""
🌟 **HSC RESULT 2025 (JASHORE)** 🌟
━━━━━━━━━━━━━━━━━━━━
👤 **Name:** {info.get('Name', 'N/A')}
👨 **Father:** {info.get('Father', 'N/A')}
🆔 **Roll:** {data['roll']} | **Reg:** {data['reg']}
📊 **Overall Status:** {info.get('Status', 'N/A')}
━━━━━━━━━━━━━━━━━━━━
📚 **Subject Wise Grade:**
{subject_list if subject_list else "_গ্রেড শীট লোড করা সম্ভব হয়নি_"}
━━━━━━━━━━━━━━━━━━━━
_Test Bot for Jashore Board_
"""
            await update.message.reply_text(result_summary, parse_mode='Markdown')
        except Exception as e:
            print(f"Scraping error: {e}")
            await update.message.reply_text("⚠️ রেজাল্ট প্রসেস করতে কিছুটা সমস্যা হয়েছে। পুনরায় চেষ্টা করুন।")
        
        data.clear()

# ---------- BOT EXECUTION ----------
if __name__ == "__main__":
    # সার্ভার সচল রাখার জন্য Flask Thread চালু করা
    keep_alive()
    
    # টেলিগ্রাম অ্যাপ্লিকেশন বিল্ড করা
    bot_app = ApplicationBuilder().token(TOKEN).build()
    
    # হ্যান্ডলার যুক্ত করা
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print(f"🚀 BOT STARTED WITH TOKEN: {TOKEN[:10]}... ✅")
    bot_app.run_polling()
