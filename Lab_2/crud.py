from flask import Flask, request, jsonify
import sqlite3
import json

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

# Read (Retrieve) with Pagination
@app.route('/products', methods=['GET'])
def get_products():
    # Get pagination parameters from query string, default to limit=5 and offset=0
    limit = request.args.get('limit', default=5, type=int)
    offset = request.args.get('offset', default=0, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch products with limit and offset
    cursor.execute("SELECT * FROM products LIMIT ? OFFSET ?", (limit, offset))
    products = cursor.fetchall()

    # Get the total count of products for pagination information
    cursor.execute("SELECT COUNT(*) FROM products")
    total_count = cursor.fetchone()[0]

    return jsonify({
        "total_count": total_count,
        "offset": offset,
        "limit": limit,
        "products": [dict(product) for product in products]
    }), 200

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

# File Upload Handler
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    # Check if the file is a JSON file
    if file.filename == '' or not file.filename.endswith('.json'):
        return jsonify({"error": "Invalid file type, please upload a JSON file"}), 400

    # Read and parse the JSON file
    try:
        data = json.load(file)

        # Extract data from JSON and insert into the database
        name = data.get('name')
        price = data.get('price')
        link = data.get('link')
        additional_info = data.get('additional_info')

        # Insert data into the database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''INSERT INTO products (name, price, link, additional_info)
                          VALUES (?, ?, ?, ?)''', (name, price, link, additional_info))
        conn.commit()
        conn.close()

        return jsonify({"message": "Product uploaded and saved successfully"}), 201
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse JSON file"}), 400

if __name__ == '__main__':
    app.run(debug=True)