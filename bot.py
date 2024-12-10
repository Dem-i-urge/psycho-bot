from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest, TimedOut, NetworkError
import os
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

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
                "✅ Спасибо за ваш вопрос! Он передан психологу.\n\n"
                "Наиболее интересные вопросы будут разобраны в постах канала.\n"
                "Для нового вопроса используйте команду /start"
            )
            
            context.user_data['waiting_for_question'] = False
            
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

def main() -> None:
    """Запускает бота"""
    try:
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))

        logger.info("Bot started")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise e

if __name__ == '__main__':
    main()
