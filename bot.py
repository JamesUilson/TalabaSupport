from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import logging
import json
import os

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Bot tokeni
BOT_TOKEN = "8444722517:AAF8M6mFvP0rPvFJ7H5gNVzJDOIFeIz9q3Q"
# Admin ID lari
ADMIN_IDS = [2110945697, 1828573198]

# JSON fayl nomi
DATA_FILE = "user_data.json"

# Global ma'lumotlarni saqlash
user_data_storage = {}
admin_reply_mode = {}  # {admin_id: target_user_id}

# Ma'lumotlarni JSON fayldan o'qish
def load_data():
    global user_data_storage
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                user_data_storage = json.load(f)
            # JSON string ID larni int ga o'tkazish
            user_data_storage = {int(k): v for k, v in user_data_storage.items()}
            print(f"✅ Ma'lumotlar fayldan yuklandi. {len(user_data_storage)} ta foydalanuvchi")
        else:
            user_data_storage = {}
            print("📁 Yangi ma'lumotlar fayli yaratildi")
    except Exception as e:
        print(f"❌ Ma'lumotlarni yuklashda xatolik: {e}")
        user_data_storage = {}

# Ma'lumotlarni JSON faylga saqlash
def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_data_storage, f, ensure_ascii=False, indent=2)
        print(f"💾 Ma'lumotlar saqlandi. {len(user_data_storage)} ta foydalanuvchi")
    except Exception as e:
        print(f"❌ Ma'lumotlarni saqlashda xatolik: {e}")

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id in ADMIN_IDS:
        await update.message.reply_text("👋 Admin paneliga xush kelibsiz!")
        return
    
    if user_id not in user_data_storage:
        user_data_storage[user_id] = {
            'messages': [],
            'replies': [],
            'username': update.message.from_user.username,
            'first_name': update.message.from_user.first_name
        }
        save_data()  # 🔄 Yangi foydalanuvchini saqlash
    
    await update.message.reply_text(
        "Assalomu alaykum! Talaba Support 24/7 dasturiga hush kelibsiz. Har qanday savol, shikoyat yoki takliflaringizni yozishingiz mumkin. Muhimi barchasi anonim tarzda jonatiladi!"
    )

# Foydalanuvchi savollarini qabul qilish
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Agar admin bo'lsa va reply rejimida bo'lsa
    if user_id in ADMIN_IDS and user_id in admin_reply_mode:
        await handle_admin_reply(update, context)
        return
    
    if user_id in ADMIN_IDS:
        return
    
    if user_id not in user_data_storage:
        user_data_storage[user_id] = {
            'messages': [],
            'replies': [],
            'username': update.message.from_user.username,
            'first_name': update.message.from_user.first_name
        }
    
    if update.message.text and update.message.text.startswith('/'):
        return
    
    question = update.message.text
    user_data_storage[user_id]['messages'].append(question)
    save_data()  # 🔄 Xabarni saqlash
    
    await send_to_admins(context, user_id, question)
    await update.message.reply_text("✅ Savolingiz qabul qilindi. Tez orada javob beramiz.")

# Adminlarga xabar yuborish
async def send_to_admins(context: ContextTypes.DEFAULT_TYPE, user_id: int, question: str):
    user_data = user_data_storage[user_id]
    
    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 Profilga o'tish", url=f"tg://user?id={user_id}"),
            InlineKeyboardButton("📝 Javob berish", callback_data=f"reply_{user_id}")
        ],
        [
            InlineKeyboardButton("📋 Xabarlar tarixi", callback_data=f"history_{user_id}"),
            InlineKeyboardButton("❌ Yopish", callback_data=f"close_{user_id}")
        ]
    ])
    
    message_text = f"""📩 Yangi savol

👤 Foydalanuvchi: {user_data['first_name']}
📱 Username: @{user_data['username'] or 'Mavjud emas'}
❓ Savol: {question}
🆔 ID: {user_id}"""
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=message_text,
                reply_markup=admin_keyboard
            )
            print(f"✅ Xabar admin {admin_id} ga yuborildi")
        except Exception as e:
            print(f"❌ Adminga xabar yuborishda xatolik: {e}")

# Callback query handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    await query.answer()
    
    if data.startswith("reply_"):
        user_id = data.split("_")[1]
        await start_reply(query, context, user_id)
    
    elif data.startswith("history_"):
        user_id = data.split("_")[1]
        await show_history(query, context, user_id)
    
    elif data.startswith("close_"):
        user_id = data.split("_")[1]
        await close_ticket(query, context, user_id)
    
    elif data.startswith("back_"):
        user_id = data.split("_")[1]
        await back_to_main(query, context, user_id)

# Xabarlar tarixi
async def show_history(query, context, user_id):
    try:
        user_id_int = int(user_id)
        
        if user_id_int not in user_data_storage:
            await query.edit_message_text("❌ Foydalanuvchi ma'lumotlari topilmadi.")
            return
        
        user_data = user_data_storage[user_id_int]
        user_messages = user_data.get('messages', [])
        admin_replies = user_data.get('replies', [])
        
        history_text = f"""📋 Xabarlar tarixi

👤 Foydalanuvchi: {user_data['first_name']}
🆔 ID: {user_id}

📝 Foydalanuvchi xabarlari:"""
        
        for i, msg in enumerate(user_messages, 1):
            history_text += f"\n{i}. {msg}"
        
        history_text += "\n\n📨 Admin javoblari:"
        
        for i, reply in enumerate(admin_replies, 1):
            history_text += f"\n{i}. {reply}"
        
        if not admin_replies:
            history_text += "\nHozircha javob yo'q"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Profilga o'tish", url=f"tg://user?id={user_id}")],
            [InlineKeyboardButton("📝 Javob berish", callback_data=f"reply_{user_id}")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data=f"back_{user_id}")]
        ])
        
        await query.edit_message_text(history_text, reply_markup=keyboard)
        
    except Exception as e:
        await query.edit_message_text(f"❌ Xatolik: {e}")

# Javob berishni boshlash
async def start_reply(query, context, user_id):
    admin_id = query.from_user.id
    admin_reply_mode[admin_id] = user_id
    
    print(f"🔵 Admin {admin_id} foydalanuvchi {user_id} ga javob berish rejimiga o'tdi")
    
    await query.edit_message_text(
        f"🆔 {user_id} foydalanuvchiga javob yozing:\n\nEndi javobingizni yozing va yuboring..."
    )

# Ticketni yopish
async def close_ticket(query, context, user_id):
    try:
        user_id_int = int(user_id)
        
        try:
            await context.bot.send_message(
                chat_id=user_id_int,
                text="❌ Sizning so'rovingiz yopildi. Yangi savol uchun /start ni bosing."
            )
        except Exception as e:
            print(f"❌ Foydalanuvchiga yopish xabarini yuborishda xatolik: {e}")
        
        await query.edit_message_text(f"✅ Ticket yopildi. Foydalanuvchi {user_id} ga xabar yuborildi.")
        
    except Exception as e:
        await query.edit_message_text(f"❌ Xatolik: {e}")

# Orqaga tugmasi
async def back_to_main(query, context, user_id):
    user_id_int = int(user_id)
    
    if user_id_int not in user_data_storage:
        await query.edit_message_text("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return
    
    user_data = user_data_storage[user_id_int]
    last_message = user_data['messages'][-1] if user_data['messages'] else "Xabar yo'q"
    
    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 Profilga o'tish", url=f"tg://user?id={user_id}"),
            InlineKeyboardButton("📝 Javob berish", callback_data=f"reply_{user_id}")
        ],
        [
            InlineKeyboardButton("📋 Xabarlar tarixi", callback_data=f"history_{user_id}"),
            InlineKeyboardButton("❌ Yopish", callback_data=f"close_{user_id}")
        ]
    ])
    
    message_text = f"""📩 Foydalanuvchi savoli

👤 Foydalanuvchi: {user_data['first_name']}
📱 Username: @{user_data['username'] or 'Mavjud emas'}
❓ Oxirgi savol: {last_message}
🆔 ID: {user_id}"""
    
    await query.edit_message_text(message_text, reply_markup=admin_keyboard)

# Admin javoblarini qabul qilish
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    print(f"🔵 Admin {user_id} dan xabar keldi: {update.message.text}")
    
    # Agar admin javob berish rejimida bo'lsa
    if user_id in admin_reply_mode:
        target_user_id = admin_reply_mode[user_id]
        admin_reply = update.message.text
        
        print(f"🔵 Admin {user_id} foydalanuvchi {target_user_id} ga javob yozmoqchi: {admin_reply}")
        
        try:
            target_user_id_int = int(target_user_id)
            
            # Foydalanuvchiga javob yuborish
            await context.bot.send_message(
                chat_id=target_user_id_int,
                text=f"📨 Admin javobi:\n\n{admin_reply}"
            )
            print(f"✅ Xabar {target_user_id_int} ga MUVAFFAQIYATLI yuborildi!")
            
            # Saqlash
            if target_user_id_int not in user_data_storage:
                user_data_storage[target_user_id_int] = {
                    'messages': [], 'replies': [admin_reply],
                    'username': '', 'first_name': ''
                }
            else:
                if 'replies' not in user_data_storage[target_user_id_int]:
                    user_data_storage[target_user_id_int]['replies'] = []
                user_data_storage[target_user_id_int]['replies'].append(admin_reply)
            
            save_data()  # 🔄 Javobni saqlash
            
            await update.message.reply_text("✅ Javob foydalanuvchiga yuborildi!")
            
            # Rejimdan chiqaramiz
            del admin_reply_mode[user_id]
            
        except Exception as e:
            error_msg = f"❌ Xatolik: {e}"
            await update.message.reply_text(error_msg)
            print(error_msg)

# Xatolik handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Xatolik: {context.error}")

# Asosiy funksiya
def main():
    # Ma'lumotlarni fayldan yuklash
    load_data()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    print("🚀 Bot ishga tushdi...")
    print(f"🔧 Adminlar: {ADMIN_IDS}")
    print(f"📊 Yuklangan foydalanuvchilar: {len(user_data_storage)}")
    application.run_polling()

if __name__ == "__main__":
    main()