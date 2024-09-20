from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3

# Токен бота та назва каналу
BOT_TOKEN = '6910578431:AAFRv8lbxWXvmDOmrPPPc2gob9GztldQFME'
CHANNEL_ID = '@ReferralAssistant'

# Ініціалізація бази даних
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

# Функція обробки нових повідомлень
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    message_text = update.message.text
    
    # Перевіряємо, чи є повідомлення посиланням
    if 'http://' in message_text or 'https://' in message_text:
        save_link(user_id, username, message_text)
        # Відправляємо посилання до каналу
        await context.bot.send_message(chat_id=CHANNEL_ID, text=message_text)
        await update.message.reply_text('Посилання отримано та відправлено в канал!')
    else:
        await update.message.reply_text('Будь ласка, відправте посилання.')

# Збереження посилання у базу даних
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

# Команда статистики для користувача
async def stats(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    conn = sqlite3.connect('links.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT link_count FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if result:
        link_count = result[0]
        await update.message.reply_text(f'Ви надіслали {link_count} посилань.')
    else:
        await update.message.reply_text('Ви ще не надсилали жодного посилання.')
    
    conn.close()

# Основна функція
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привіт! Надсилайте свої посилання.")

# Запуск бота
def main():
    init_db()
    
    # Створення екземпляра Application замість Updater
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обробка команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    
    # Обробка повідомлень з посиланнями
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
