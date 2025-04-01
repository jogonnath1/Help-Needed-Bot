import logging
from telegram import Update, ChatMember
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackContext

# 🔹 Bot Token
BOT_TOKEN = "7719373493:AAHtw9VPP4J636VS1yzL0fLKzSpPsAMFWCE"

# 🔹 নির্দিষ্ট গ্রুপের ID
ALLOWED_CHAT_ID = -1002483552499

# 🔹 লগিং সেটআপ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# 🔹 গ্রুপের মেম্বারদের আইডি সংরক্ষণ করতে একটি সেট
group_members = set()

async def fetch_group_members(context: CallbackContext) -> None:
    """বট রিস্টার্ট হলে গ্রুপের সদস্যদের আইডি সংগ্রহ করবে"""
    try:
        chat_members = await context.bot.get_chat_administrators(ALLOWED_CHAT_ID)
        for member in chat_members:
            group_members.add(member.user.id)

        logging.info(f"✅ গ্রুপের মেম্বার লোড হয়েছে: {len(group_members)} জন")
    except Exception as e:
        logging.warning(f"❌ গ্রুপ মেম্বার লোড করতে সমস্যা: {e}")

async def send_alert(update: Update, context: CallbackContext) -> None:
    """শুধু নির্দিষ্ট গ্রুপে যদি #help মেসেজ থাকে, তাহলে মেম্বারদের ইনবক্সে পাঠাবে"""
    if update.message.chat.id != ALLOWED_CHAT_ID:
        return  # ভুল গ্রুপ হলে কিছু করবে না

    message_text = update.message.text
    if "#help" in message_text.lower():
        sender = update.message.from_user
        sender_name = sender.full_name

        failed_users = []  # যাদের ইনবক্সে পাঠানো যায়নি তাদের তালিকা

        for user_id in group_members:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🆘 {sender_name} এর জরুরি সাহায্য প্রয়োজন!"
                )
            except Exception as e:
                logging.warning(f"❌ {user_id} কে মেসেজ পাঠানো যায়নি: {e}")
                failed_users.append(f"[User](tg://user?id={user_id})")

        # যাদের ইনবক্সে মেসেজ পাঠানো যায়নি, তাদের গ্রুপে নোটিফাই করা হবে
        if failed_users:
            mention_list = ", ".join(failed_users)
            await context.bot.send_message(
                chat_id=ALLOWED_CHAT_ID,
                text=f"🆘 {sender_name} এর জরুরি সাহায্য প্রয়োজন। নিচের ইউজাররা বটের সাথে `/start` লিখে চ্যাট শুরু করুন! 👇\n{mention_list}",
                parse_mode="Markdown"
            )

async def start(update: Update, context: CallbackContext) -> None:
    """যখন কেউ /start কমান্ড পাঠাবে, তখন তাদের আইডি সংরক্ষণ করবে"""
    user = update.message.from_user
    group_members.add(user.id)
    await update.message.reply_text("✅ তুমি এখন সাবস্ক্রাইব করেছো! 🆘 গ্রুপে কেউ #help লিখলে তুমি নোটিফিকেশন পাবে।")

async def member_update(update: Update, context: CallbackContext) -> None:
    """যখন নতুন সদস্য গ্রুপে যোগ হবে, তখন তাকে সংরক্ষণ করা হবে"""
    chat_member = update.chat_member
    if chat_member.new_chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]:
        group_members.add(chat_member.new_chat_member.user.id)

async def init_jobs(app: Application) -> None:
    """বট চালু হলে গ্রুপের মেম্বার লোড করবে"""
    await fetch_group_members(CallbackContext(app))

def main():
    """বট চালু করার জন্য মেইন ফাংশন"""
    app = Application.builder().token(BOT_TOKEN).post_init(init_jobs).build()

    # ✅ /start কমান্ড হ্যান্ডলার
    app.add_handler(CommandHandler("start", start))

    # ✅ নতুন সদস্য যোগ হলে সংরক্ষণ করবে
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, member_update))

    # ✅ মেসেজ ফরোয়ার্ডার হ্যান্ডলার (#help মেসেজ পাঠালে কাজ করবে)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_alert))

    # ✅ বট চালু করা
    logging.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
