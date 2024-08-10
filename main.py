import random
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
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
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
    await update.message.reply_text('Here are some commands you can use:\n/start - Start the bot\n/help - Get help\n/balance - Check your balance\n/bet - Place a bet\n/deposit - Add funds to your account')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat.id)
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        balance = user.balance if user else 0.0
    await update.message.reply_text(f'Your balance is {balance}€')

async def bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("20€", callback_data='bet_20')],
        [InlineKeyboardButton("40€", callback_data='bet_40')],
        [InlineKeyboardButton("100€", callback_data='bet_100')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select an amount to bet:", reply_markup=reply_markup)

async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("20€", callback_data='deposit_20')],
        [InlineKeyboardButton("40€", callback_data='deposit_40')],
        [InlineKeyboardButton("100€", callback_data='deposit_100')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select an amount to deposit:", reply_markup=reply_markup)

# handlers
async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.message.chat.id)
    bet_amount = int(query.data.split('_')[1])
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        balance = user.balance if user else 0.0
        
        if bet_amount > balance:
            await query.message.reply_text(f'You cannot bet more than your balance, which currently sits at {balance}')
            return
        
        if random.random() >= 0.5:
            user.balance -= bet_amount
            db.session.commit()
            await query.message.reply_text(f'You have bet {bet_amount}€ and lost. Your new balance is {user.balance}€')
        else:
            user.balance += bet_amount
            db.session.commit()
            await query.message.reply_text(f'You have bet {bet_amount}€ and won! Your new balance is {user.balance}€')


async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.message.chat.id
    amount = int(query.data.split('_')[1])

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': 'Deposit to Gamblr'},
                'unit_amount': 100*amount,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url = f'https://127.0.0.1:5001/success?user_id={user_id}&amount={amount}',
        cancel_url = 'https://127.0.0.1:5001/cancel'
    )
    await query.message.reply_text(f"Please complete your payment: {session.url}")

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
    telegram_app.add_handler(CommandHandler('deposit', deposit_command))

    # callback for inline buttons
    telegram_app.add_handler(CallbackQueryHandler(handle_bet, pattern='^bet_'))
    telegram_app.add_handler(CallbackQueryHandler(handle_deposit, pattern='^deposit_'))

    # messages
    telegram_app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # errors
    telegram_app.add_error_handler(error)

    # polling
    print('Polling')
    telegram_app.run_polling(poll_interval=5)