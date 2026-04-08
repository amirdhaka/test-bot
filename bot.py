import requests
from bs4 import BeautifulSoup
import urllib3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ----------- CONFIGURATION -----------
BOT_TOKEN = "8723976334:AAE0vOE-tZ7pZvJXBTLNUYI1ozoxvOL0tp0"

# আপনার নতুন স্ক্রিনশট অনুযায়ী এই কোডটি আপডেট করা হয়েছে
CPO_PARAM = "aHR0cHM6Ly9iYmdnYy5lc2hpa3NhZW1zLmNvbQ" 

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Referer": f"https://108.181.90.163/index.php?__cpo={CPO_PARAM}"
}

def get_student_and_photo(roll):
    session = requests.Session()
    session.verify = False
    
    # প্রথমে লগইন সেশন তৈরি করা
    login_url = f"https://108.181.90.163/login.php?__cpo={CPO_PARAM}"
    login_payload = {
        "username": "bbggcstudent",
        "password": "bbggcstudent",
        "login": "Sign In"
    }
    
    try:
        # লগইন করা
        session.post(login_url, data=login_payload, headers=headers, timeout=15)
        
        # ডাটা সার্চ করা
        search_url = f"https://108.181.90.163/Basic-Result-Enquiry-Center?roll={roll}&__cpo={CPO_PARAM}"
        response = session.get(search_url, headers=headers, timeout=15)
        
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        
        if table:
            rows = table.find_all("tr")
            if len(rows) >= 2:
                cols = rows[1].find_all("td")
                
                # ফটোর লিঙ্ক (সার্ভারের লুকানো ফোল্ডার চেক)
                photo = f"https://108.181.90.163/assets/students_picture/{roll}.jpg?__cpo={CPO_PARAM}"
                
                return {
                    "Name": cols[0].get_text(strip=True),
                    "Roll": roll,
                    "Type": cols[3].get_text(strip=True),
                    "Amount": cols[4].get_text(strip=True),
                    "Photo": photo
                }
        return None
    except:
        return None

# ----------- BOT HANDLER -----------
async def handle_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roll = update.message.text.strip()
    if not roll.isdigit(): return

    msg = await update.message.reply_text(f"⏳ সেশন চেক করা হচ্ছে... {roll} এর ছবি খোঁজা হচ্ছে।")
    data = get_student_and_photo(roll)
    
    if data:
        caption = (
            f"🎓 <b>BBGGC Student Details</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>নাম:</b> {data['Name']}\n"
            f"🔢 <b>রোল:</b> {data['Roll']}\n"
            f"💰 <b>পরিমাণ:</b> {data['Amount']} BDT\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        
        try:
            # ছবিসহ তথ্য পাঠানো
            await update.message.reply_photo(photo=data["Photo"], caption=caption, parse_mode="HTML")
        except:
            # ছবি না পেলে শুধু তথ্য
            await update.message.reply_text(caption + "\n⚠️ ছবি সার্ভারে হাইড করা আছে।", parse_mode="HTML")
        await msg.delete()
    else:
        await msg.edit_text("❌ সেশন এরর! ব্রাউজারে গিয়ে CroxyProxy থেকে নতুন লিঙ্ক কপি করে বসান।")

if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("রোল পাঠান।")))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_roll))
    application.run_polling()
