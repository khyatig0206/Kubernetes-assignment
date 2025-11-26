from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# ❌ No fallback values here
mongo_user = os.environ["MONGO_USERNAME"]
mongo_pass = os.environ["MONGO_PASSWORD"]
mongo_host = os.environ["MONGO_HOST"]
mongo_port = os.environ["MONGO_PORT"]

mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/"

client = MongoClient(mongo_uri)
db = client.flask_db
collection = db.data

@app.route('/')
def index():
    return f"Welcome to the Flask app! The current time is: {datetime.now()}"

@app.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        entry = request.get_json()
        collection.insert_one(entry)
        return jsonify({"status": "Data inserted"}), 201
    else:
        items = list(collection.find({}, {"_id": 0}))
        return jsonify(items), 200

@app.route('/load')
def load():
    x = 0
    for i in range(1000_000_000):  # more iterations → more CPU
        x += i
    return str(x)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
