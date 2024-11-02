from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Database helper function
def get_db_connection():
    conn = sqlite3.connect("products.db")
    conn.row_factory = sqlite3.Row  # Allows us to return rows as dictionaries
    return conn

# Create (Insert)
@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    link = data.get('link')
    additional_info = data.get('additional_info')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''INSERT INTO products (name, price, link, additional_info) 
                          VALUES (?, ?, ?, ?)''', (name, price, link, additional_info))
        conn.commit()
        return jsonify({"message": "Product created successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "Product already exists"}), 400
    finally:
        conn.close()

# Read (Retrieve)
@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return jsonify([dict(product) for product in products]), 200

# Update
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    additional_info = data.get('additional_info')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''UPDATE products SET name = ?, price = ?, additional_info = ? WHERE id = ?''',
                   (name, price, additional_info, product_id))
    conn.commit()

    if cursor.rowcount == 0:
        return jsonify({"message": "Product not found"}), 404

    return jsonify({"message": "Product updated successfully"}), 200

# Delete
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()

    if cursor.rowcount == 0:
        return jsonify({"message": "Product not found"}), 404

    return jsonify({"message": "Product deleted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)