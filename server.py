from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from dotenv import load_dotenv

load_dotenv()

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

if __name__ == '__main__':
    app.run()
