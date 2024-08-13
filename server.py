from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import os
import random
import stripe
import logging
from dotenv import load_dotenv

load_dotenv()
base_url = os.getenv('BASE_URL', '127.0.0.1:5001')

# Initialize Flask app and SQLite database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f"<User {self.telegram_id}, Balance {self.balance}>"

# Create the database and table
with app.app_context():
    db.create_all()

@app.route('/success', methods=['GET'])
def success():
    user_id = request.args.get('user_id')
    amount = float(request.args.get('amount'))
    
    if not user_id or not amount:
        logger.error('Missing user_id or amount parameter')
        return "Missing user_id or amount parameter.", 400

    # Update user balance in the database
    user = User.query.filter_by(telegram_id=user_id).first()
    if user:
        user.balance += amount
        db.session.commit()
        logger.info(f'Updated user {user_id} balance by {amount}€. New balance: {user.balance}€')
        return f"Success! Your balance has been updated by {amount}€."
    else:
        logger.warning(f'User not found: {user_id}')
        return "User not found.", 404

@app.route('/cancel', methods=['GET'])
def cancel():
    return "Payment canceled."

@app.route('/create_checkout_session', methods=['POST'])
def create_checkout_session():
    data = request.json
    user_id = data['user_id']
    amount = data['amount']

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
        success_url=f'https://{base_url}/success?user_id={user_id}&amount={amount}',
        cancel_url=f'https://{base_url}/cancel'
    )
    
    return {'checkout_url': session.url}

@app.route('/get_balance', methods=['GET'])
def get_balance():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return {"error": "Missing user_id parameter"}, 400
    
    user = User.query.filter_by(telegram_id=user_id).first()
    if user:
        return {"balance": user.balance}, 200
    else:
        return {"error": "User not found"}, 404

@app.route('/place_bet', methods=['POST'])
def place_bet():
    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount')

    if not user_id or not amount:
        return {"success": False, "message": "Missing user_id or amount"}, 400

    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if not user:
            return {"success": False, "message": "User not found"}, 404
        
        if amount > user.balance:
            return {"success": False, "message": "Insufficient balance"}, 400
        
        # Simulate a bet
        if random.random() >= 0.5:
            user.balance -= amount
            result_message = f'You lost {amount}€'
        else:
            user.balance += amount
            result_message = f'You won {amount}€'

        db.session.commit()
        return {"success": True, "message": result_message, "new_balance": user.balance}, 200

if __name__ == '__main__':
    app.run(port=5001)