# Forward Save Bot - Final Version (Auto-forward to Bot + Admin Group, Replit 24/7 Ready)
# Author: ChatGPT x You
# Purpose: Collect forwarded messages, resend to chat, secretly forward to admin group, admin-only commands, keep alive with Flask

import logging
import sqlite3
import time
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ====== SETTINGS ======

BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token
ADMIN_USER_ID = 6923921695  # Your Telegram User ID
ADMIN_GROUP_ID = -1002341543137  # Your admin group/channel ID with minus sign
DB_PATH = "forwarded_messages.db"
START_TIME = time.time()

# ====== FLASK KEEP ALIVE ======

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

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

# ====== HELPER FUNCTION ======

def is_admin(user_id):
    return user_id == ADMIN_USER_ID

# ====== BOT HANDLERS ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Forward me any message and I will forward the message back.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commands:\n/start - Welcome\n/help - Help\n/status - Admin only\n/getall - Admin only")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    now = time.time()
    uptime_seconds = int(now - START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM forwarded')
    saved_messages = c.fetchone()[0]
    conn.close()

    reply = (
        f"✅ Bot Online\n"
        f"💬 Messages Saved: {saved_messages}\n"
        f"⏱️ Uptime: {hours}h {minutes}m {seconds}s"
    )

    await update.message.reply_text(reply)

async def getall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, username, message_text, file_id, timestamp FROM forwarded ORDER BY timestamp DESC LIMIT 10')
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No saved messages yet.")
        return

    for row in rows:
        text = f"ID: {row[0]}\nUser: @{row[1]}\nText: {row[2]}\nMedia ID: {row[3]}\nTime: {row[4]}"
        await update.message.reply_text(text)

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

    try:
        await update.message.copy(chat_id=update.message.chat_id)
    except Exception as e:
        print(f"Failed to copy to user chat: {e}")

    try:
        await update.message.copy(chat_id=ADMIN_GROUP_ID)
    except Exception as e:
        print(f"Failed to copy to Admin Group: {e}")

# ====== MAIN ======

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("getall", getall))
    app.add_handler(MessageHandler(filters.ALL, forward_handler))

    app.run_polling()

if __name__ == '__main__':
    keep_alive()
    main()
