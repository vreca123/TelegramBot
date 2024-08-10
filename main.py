import os
from dotenv import load_dotenv
import stripe
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from model import Database, create_user_schema

load_dotenv()

# Initialize Database
db = Database('mongodb+srv://timvrecic:fxTj25E7@cluster1.2jux2.mongodb.net/')

# environment variables
TOKEN = os.getenv('TOKEN')
BOT_USERNAME = '@best_gamblr_bot'
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat.id)
    
    # Check if the user already exists
    user = db.find_user_by_telegram_id(user_id)
    if not user:
        user = create_user_schema(user_id)
        db.insert_user(user)
    
    await update.message.reply_text('Hello, welcome to Gamblr!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Here are some commands you can use:\n/start - Start the bot\n/help - Get help\n/balance - Check your balance\n/bet - Place a bet')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat.id)
    user = db.find_user_by_telegram_id(user_id)
    balance = user['balance'] if user else 0.0
    await update.message.reply_text(f'Your balance is {balance}€')

async def bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Open the web app for bets
    await update.message.reply_text(
        "Opening bet interface...",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="Open Bet Interface",
                web_app={"url": "https://vreca123.github.io/TelegramBot/index.html"}
            )
        ]])
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    response = 'See /help for further information on commands.'
    print('Bot:', response)
    await update.message.reply_text(response)

# Logging
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Running')
    telegram_app = Application.builder().token(TOKEN).build()

    # Commands
    telegram_app.add_handler(CommandHandler('start', start_command))
    telegram_app.add_handler(CommandHandler('help', help_command))
    telegram_app.add_handler(CommandHandler('balance', balance_command))
    telegram_app.add_handler(CommandHandler('bet', bet_command))

    # Messages
    telegram_app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    telegram_app.add_error_handler(error)

    # Polling
    print('Polling')
    telegram_app.run_polling(poll_interval=5)