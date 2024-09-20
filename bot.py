from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3

def init_db():
    conn = sqlite3.connect('links.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            link TEXT,
            clicks INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            link_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    message_text = update.message.text
    
    if 'http://' in message_text or 'https://' in message_text:
        save_link(user_id, username, message_text)
        context.bot.send_message(chat_id='@ReferralAssistant', text=message_text)
        update.message.reply_text('Посилання отримано та відправлено в канал!')
    else:
        update.message.reply_text('Будь ласка, відправте посилання.')

def save_link(user_id, username, link):
    conn = sqlite3.connect('links.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO links (user_id, username, link) VALUES (?, ?, ?)
    ''', (user_id, username, link))
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, link_count) VALUES (?, ?, 0)
    ''', (user_id, username))
    cursor.execute('''
        UPDATE users SET link_count = link_count + 1 WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

def stats(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    conn = sqlite3.connect('links.db')
    cursor = conn.cursor()
    cursor.execute('SELECT link_count FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        link_count = result[0]
        update.message.reply_text(f'Ви надіслали {link_count} посилань.')
    else:
        update.message.reply_text('Ви ще не надсилали жодного посилання.')
    conn.close()

def main():
    init_db()
    updater = Updater("YOUR_BOT_TOKEN", use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Привіт! Надсилайте свої посилання.")))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
