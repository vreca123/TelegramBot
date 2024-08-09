from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask app and SQLite database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gamblr.db'  # SQLite database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

@app.route('/success')
def success():
    user_id = request.args.get('user_id')
    amount = float(request.args.get('amount'))
    
    # Update user balance in the database
    user = User.query.filter_by(telegram_id=user_id).first()
    if user:
        user.balance += amount
        db.session.commit()
        return f"Success! Your balance has been updated by {amount}€."
    else:
        return "User not found.", 404

@app.route('/cancel')
def cancel():
    return "Payment canceled."

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_ENV') == 'development', port=os.getenv('FLASK_RUN_PORT', 5000))
