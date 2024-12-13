from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database Initialization
def init_db():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        price TEXT,
                        link TEXT UNIQUE,
                        additional_info TEXT
                    )''')
    conn.commit()
    conn.close()

@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    link = data.get('link')
    additional_info = data.get('additional_info', '')

    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''INSERT INTO products (name, price, link, additional_info) VALUES (?, ?, ?, ?)''',
                       (name, price, link, additional_info))
        conn.commit()
        return jsonify({"message": "Product created successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "Product already exists"}), 400
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    app.run(port=5000)