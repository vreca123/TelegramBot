from flask import Flask, request, jsonify
import os
import stripe
from dotenv import load_dotenv
from model import Database, create_payment_schema, create_user_schema

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
db = Database('mongodb+srv://timvrecic:fxTj25E7@cluster1.2jux2.mongodb.net/')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    data = request.get_json()
    try:
        intent = stripe.PaymentIntent.create(
            amount=data['amount'],
            currency=data['currency']
        )
        return jsonify({'clientSecret': intent.client_secret})
    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route('/webhook', methods=['POST'])
def webhook_received():
    event = request.get_json()

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        user_id = payment_intent['metadata']['user_id']
        amount = payment_intent['amount']

        # Create a payment record in the database
        payment = create_payment_schema(user_id, amount, 'succeeded')
        db.insert_payment(payment)

        # Update the user's balance
        user = db.find_user_by_id(user_id)
        new_balance = user['balance'] + amount
        db.db.users.update_one({'_id': user_id}, {'$set': {'balance': new_balance}})

    return jsonify(success=True)

@app.route('/balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    user = db.find_user_by_id(user_id)
    if user:
        return jsonify({"balance": user['balance']})
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/create-user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    user = create_user_schema(username)
    user_id = db.insert_user(user)
    return jsonify({"user_id": str(user_id)})

if __name__ == '__main__':
    app.run(port=5001)