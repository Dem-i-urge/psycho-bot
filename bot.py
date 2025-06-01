from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest, TimedOut, NetworkError
import os
from datetime import datetime
import logging
import asyncio
from flask import Flask, request
import threading

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
PORT = int(os.getenv("PORT", 5000))

# Проверяем переменные окружения
if not TOKEN:
    logger.error("No BOT_TOKEN provided")
    raise ValueError("No BOT_TOKEN provided")

if not ADMIN_ID:
    logger.error("No ADMIN_ID provided")
    raise ValueError("No ADMIN_ID provided")

# Flask приложение для health check
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    """Запускает Flask сервер в отдельном потоке"""
    app.run(host='0.0.0.0', port=PORT)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и кнопку для отправки вопроса"""
    try:
        keyboard = [
            [InlineKeyboardButton("Задать вопрос", callback_data='ask_question')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """🌟 Добро пожаловать в "Психо и точка"!

Здесь вы можете задать интересующий вас вопрос.

❗️ Обратите внимание:
- Это не экстренная психологическая помощь
- На личные вопросы отвечаю в формате платной консультации
- Наиболее интересные вопросы будут разобраны в постах канала

Нажмите кнопку "Задать вопрос" ниже 👇"""

        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        logger.info(f"Start command from user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатие кнопки"""
    try:
        query = update.callback_query
        await query.answer()

        await query.message.reply_text(
            "📝 Пожалуйста, напишите ваш вопрос в следующем сообщении.\n\n"
            "Постарайтесь сформулировать его максимально конкретно."
        )
        context.user_data['waiting_for_question'] = True
        logger.info(f"Question request from user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error in button handler: {e}")

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает полученный вопрос"""
    try:
        if context.user_data.get('waiting_for_question'):
            question = update.message.text
            user = update.message.from_user
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            admin_message = (
                f"❓ Новый вопрос!\n\n"
                f"От: @{user.username if user.username else 'Анонимный пользователь'}\n"
                f"ID: {user.id}\n"
                f"Время: {timestamp}\n\n"
                f"Вопрос:\n{question}"
            )
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message
            )
            
            await update.message.reply_text(
                "✅ Спасибо за ваш вопрос! Он передан специалисту.\n\n"
                "Наиболее интересные вопросы будут разобраны в постах канала.\n"
                "Для нового вопроса используйте команду /start"
            )
            
            context.user_data['waiting_for_question'] = False
            logger.info(f"Question received from user {user.id}")
            
    except Exception as e:
        logger.error(f"Error in handle_question: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обработке вопроса. Пожалуйста, попробуйте позже или используйте команду /start"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение с помощью при команде /help"""
    help_text = """🔍 Как пользоваться ботом:

1. Нажмите кнопку "Задать вопрос"
2. Напишите ваш вопрос в следующем сообщении
3. Дождитесь подтверждения получения

❗️ Важно:
- Бот не предназначен для экстренной помощи
- Для личной консультации обратитесь к специалисту
- Ответы на интересные вопросы публикуются в канале

Для начала работы введите /start"""
    
    await update.message.reply_text(help_text)

async def run_bot():
    """Запускает бота"""
    try:
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))

        logger.info("Bot starting...")
        await application.initialize()
        await application.start()
        
        # Запускаем polling
        await application.updater.start_polling()
        logger.info("Bot started successfully!")
        
        # Держим бота активным
        while True:
            await asyncio.sleep(1)
        
    except Exception as e:
        logger.error(f"Error in bot: {e}")
        raise e

def main():
    """Главная функция"""
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info(f"Flask server started on port {PORT}")
    
    # Запускаем бота
    asyncio.run(run_bot())

if __name__ == '__main__':
    main()
