import logging
from difflib import SequenceMatcher
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# আপনার প্রদানকৃত টেলিগ্রাম বট টোকেন
TOKEN = "8951438962:AAEnQ9105wolgvz1Ok6s-JKatFMd_h8szvo"

# সাউন্ড ইফেক্ট অডিও ফাইল URL (ফ্রি নোটিফিকেশন টিউন)
SOUND_URL = "https://www.soundjay.com/buttons/sounds/button-3.mp3"

# মেমোরিতে থাকা ইউজারনেম লিস্ট (ডাটাবেজ ছাড়া হালকা রাখার জন্য)
USERNAMES_DB = [
    "rahim_official", "rahim_developer", "tamim_iqbal", "sakib_al_hasan",
    "karim_coder", "shakib_gamer", "tanvir_boss", "mahfuz_animation",
    "bangla_cartoon", "freefire_king", "pro_player_bd", "salam_animation"
]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **স্মার্ট ইউজারনেম ফাইন্ডার বটে স্বাগতম!**\n\n"
        "যেকোনো ইউজারনেমের কিছুটা মনে থাকলে তা টাইপ করে পাঠান। "
        "বট অ্যালগরিদম ব্যবহার করে সবচেয়ে কাছাকাছি মিল থাকা ইউজারনেম খুঁজে বের করবে।"
    )
    keyboard = [
        [InlineKeyboardButton("➕ নতুন নাম যোগ করুন", callback_data="add_info")],
        [InlineKeyboardButton("📜 লিস্ট দেখুন", callback_data="show_list")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def search_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip().lower().replace("@", "")
    
    if len(query) < 2:
        await update.message.reply_text("⚠️ অনুগ্রহ করে অনুসন্ধানের জন্য অন্তত ২টি অক্ষর লিখুন।")
        return

    results = []
    
    for uname in USERNAMES_DB:
        # অ্যালগরিদম দিয়ে নামের মিলের শতাংশ (Percentage) হিসাব
        ratio = SequenceMatcher(None, query, uname.lower()).ratio() * 100
        
        # আংশিক টেক্সট মিলে গেলে পয়েন্ট বাড়ানো
        if query in uname.lower():
            ratio = max(ratio, 80.0)
            
        if ratio >= 35: # ৩৫% বা তার বেশি মিল থাকলে রেজাল্টে আসবে
            results.append((uname, round(ratio)))

    # সর্বোচ্চ মিল অনুযায়ী সাজানো
    results.sort(key=lambda x: x[1], reverse=True)

    if not results:
        await update.message.reply_text("❌ কাছাকাছি কোনো ইউজারনেম পাওয়া যায়নি।")
        return

    # সাউন্ড ইফেক্ট পাঠানো
    try:
        await update.message.reply_audio(audio=SOUND_URL, caption="🔔 **ম্যাচিং রেজাল্ট প্রস্তুত!**")
    except Exception:
        pass

    # রেজাল্ট মেসেজ এবং বাটন তৈরি
    reply_text = f"🔍 **'{query}' এর জন্য সম্ভাব্য মিলসমূহ:**\n"
    keyboard = []

    for uname, match_pct in results[:5]: # শীর্ষ ৫টি রেজাল্ট দেখাবে
        reply_text += f"\n• `@{uname}` — মিল: **{match_pct}%**"
        keyboard.append([
            InlineKeyboardButton(f"👤 @{uname} ({match_pct}% Match)", url=f"https://t.me/{uname}")
        ])

    keyboard.append([InlineKeyboardButton("🔄 আবার সার্চ করুন", callback_data="retry")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(reply_text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add_info":
        await query.message.reply_text("নতুন নাম যোগ করতে এভাবে লিখুন:\n`/add username`\n\nউদাহরণ: `/add cartoon_studio`", parse_mode="Markdown")
    elif query.data == "show_list":
        names = "\n".join([f"• `@{u}`" for u in USERNAMES_DB[:20]])
        await query.message.reply_text(f"📋 **বর্তমানে সংরক্ষিত ইউজারনেমসমূহ:**\n\n{names}", parse_mode="Markdown")
    elif query.data == "retry":
        await query.message.reply_text("যেকোনো নামের আংশিক বা উল্টাপাল্টা বানান লিখে মেসেজ দিন।")

async def add_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ ইউজারনেম লিখুন। যেমন: `/add new_user`")
        return
    
    new_uname = context.args[0].strip().replace("@", "")
    if new_uname in USERNAMES_DB:
        await update.message.reply_text("⚠️ এই ইউজারনেমটি আগেই লিস্টে আছে।")
    else:
        USERNAMES_DB.append(new_uname)
        await update.message.reply_text(f"✅ `@{new_uname}` সফলভাবে যোগ করা হয়েছে!", parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_username))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_username))

    print("🤖 Bot started successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
