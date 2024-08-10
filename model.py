from pymongo import MongoClient
from bson.objectid import ObjectId

class Database:
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client['Gamblr-db']

    def insert_user(self, user):
        return self.db.users.insert_one(user).inserted_id

    def find_user_by_telegram_id(self, telegram_id):
        return self.db.users.find_one({"telegram_id": telegram_id})

    def update_user_balance(self, telegram_id, amount):
        self.db.users.update_one({"telegram_id": telegram_id}, {'$set': {'balance': amount}})

    def insert_payment(self, payment):
        return self.db.payments.insert_one(payment).inserted_id

    def find_payments_by_user(self, user_id):
        return self.db.payments.find({"user_id": ObjectId(user_id), "status": "succeeded"})

def create_user_schema(telegram_id):
    return {
        "telegram_id": telegram_id,
        "balance": 0,
    }

def create_payment_schema(user_id, amount, status):
    return {
        "user_id": ObjectId(user_id),
        "amount": amount,
        "status": status,
    }
