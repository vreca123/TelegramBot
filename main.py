import os
from dotenv import load_dotenv
import stripe
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

# Flask Setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ldShpAErqCnXkuFCeSLszukbVeAKPOZj@monorail.proxy.rlwy.net:12904/railway'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)

with app.app_context():
    db.create_all()

# environment variables
TOKEN = os.getenv('TOKEN')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
BOT_USERNAME = '@best_gamblr_bot'

stripe.api_key = STRIPE_SECRET_KEY

# commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat.id)
    
    # Check if the user already exists
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if not user:
            user = User(telegram_id=user_id, balance=0.0)
            db.session.add(user)
            db.session.commit()
    await update.message.reply_text('Hello, welcome to Gamblr!')
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Here are some commands you can use:\n/start - Start the bot\n/help - Get help\n/balance - Check your balance\n/bet - Place a bet')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat.id)
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        balance = user.balance if user else 0.0
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

# logging
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Running')
    telegram_app = Application.builder().token(TOKEN).build()

    # commands
    telegram_app.add_handler(CommandHandler('start', start_command))
    telegram_app.add_handler(CommandHandler('help', help_command))
    telegram_app.add_handler(CommandHandler('balance', balance_command))
    telegram_app.add_handler(CommandHandler('bet', bet_command))

    # messages
    telegram_app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # errors
    telegram_app.add_error_handler(error)

    # polling
    print('Polling')
    telegram_app.run_polling(poll_interval=5)