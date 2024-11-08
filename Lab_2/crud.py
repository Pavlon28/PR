from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send
import sqlite3
import threading
import json

app = Flask(__name__)
socketio = SocketIO(app)  # Initialize SocketIO for WebSocket support

# Database helper function
def get_db_connection():
    conn = sqlite3.connect("products.db")
    conn.row_factory = sqlite3.Row  # Allows us to return rows as dictionaries
    return conn

# CRUD Operations (HTTP Server)

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
    limit = request.args.get('limit', default=5, type=int)
    offset = request.args.get('offset', default=0, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products LIMIT ? OFFSET ?", (limit, offset))
    products = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM products")
    total_count = cursor.fetchone()[0]

    return jsonify({
        "total_count": total_count,
        "offset": offset,
        "limit": limit,
        "products": [dict(product) for product in products]
    }), 200

# Update (PUT)
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

# Delete (DELETE)
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()

    if cursor.rowcount == 0:
        return jsonify({"message": "Product not found"}), 404

    return jsonify({"message": "Product deleted successfully"}), 200

# Route to handle file uploads (Multipart Form Data)
# Route to handle file uploads (Multipart Form Data)
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    conn = None
    try:
        # Decode file contents to a string and parse it as JSON
        data = file.read().decode("utf-8")
        json_data = json.loads(data)

        # Check if json_data is a list
        if not isinstance(json_data, list):
            return jsonify({"message": "Uploaded file is not in expected format (should be a list of products)."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        for item in json_data:
            # Ensure each item is a dictionary
            if not isinstance(item, dict):
                return jsonify({"message": "Each product entry must be a JSON object."}), 400

            name = item.get('name')
            price = item.get('price')
            link = item.get('link')
            additional_info = item.get('additional_info', '')

            # Insert the product data into the database
            cursor.execute('''INSERT OR IGNORE INTO products (name, price, link, additional_info)
                              VALUES (?, ?, ?, ?)''', (name, price, link, additional_info))
        conn.commit()
        return jsonify({"message": "File data inserted successfully"}), 201

    except json.JSONDecodeError as e:
        return jsonify({"message": f"Error parsing file: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# WebSocket Chat Room (WebSocket Server)

@socketio.on('join')
def handle_join(data):
    # If data is a string, try parsing it as JSON
    if isinstance(data, str):
        try:
            data = json.loads(data)  # Parse the string as JSON
        except json.JSONDecodeError:
            print("Received data is not valid JSON:", data)
            return

    # Now data should be a dictionary, so you can safely access the 'username' and 'room' keys
    if isinstance(data, dict):
        username = data.get('username')
        room = data.get('room')

        if username and room:
            join_room(room)
            print(f"\033[92m{username} has joined the room {room}.\033[0m")  # Green color
            send(f"{username} has joined the room {room}.", to=room)
        else:
            print("Invalid join data received:", data)
    else:
        print("Received data is not in the expected format:", data)

@socketio.on('leave')
def handle_leave(data):
    # If data is a string, try parsing it as JSON
    if isinstance(data, str):
        try:
            data = json.loads(data)  # Parse the string as JSON
        except json.JSONDecodeError:
            print("Received data is not valid JSON:", data)
            return

    # Now data should be a dictionary, so you can safely access the 'username' and 'room' keys
    if isinstance(data, dict):
        username = data.get('username')
        room = data.get('room')

        if username and room:
            leave_room(room)
            print(f"\033[91m{username} has left the room {room}.\033[0m")  # Red color
            send(f"{username} has left the room {room}.", to=room)
        else:
            print("Invalid leave data received:", data)
    else:
        print("Received leave data is not in the expected format:", data)


@socketio.on('message')
def handle_message(data):
    # If data is a string, try parsing it as JSON
    if isinstance(data, str):
        try:
            data = json.loads(data)  # Parse the string as JSON
        except json.JSONDecodeError:
            print("Received data is not valid JSON:", data)
            return

    # Now data should be a dictionary, so you can safely access the 'room' and 'message' keys
    if isinstance(data, dict):
        room = data.get('room')
        message = data.get('message')

        if room and message:
            print(f"\033[94m[{room}] Message: {message}\033[0m")  # Blue color
            send(message, to=room)
        else:
            print("Invalid message data received:", data)
    else:
        print("Received message data is not in the expected format:", data)

def run_http_server():
    app.run(port=5000)

def run_websocket_server():
    socketio.run(app, port=5001, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    http_thread = threading.Thread(target=run_http_server)
    websocket_thread = threading.Thread(target=run_websocket_server)
    http_thread.start()
    websocket_thread.start()