import requests
from bs4 import BeautifulSoup
import sqlite3

# Connect to the SQLite database (it will create the file if it doesn't exist)
conn = sqlite3.connect("products.db")
cursor = conn.cursor()

# Create the products table
cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    price TEXT,
                    link TEXT,
                    additional_info TEXT
                )''')
conn.commit()

url = "https://ultra.md/category/tv-televizory"

# Make the GET request
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    print("Successfully retrieved HTML content.")

    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.find_all("div", class_="product-block")

    for product in products:
        try:
            name = product.find("a", class_="product-text").text
            price = " ".join(product.find("span", class_="text-blue text-xl font-bold dark:text-white").text.split())
            link = product.find("a", class_="product-text")["href"]
            response2 = requests.get(link)
            soup2 = BeautifulSoup(response2.text, "html.parser")

            # Check if the label exists before accessing its text
            info_label = soup2.find("label", class_="cursor-pointer font-semibold")
            info = info_label.text.strip() if info_label else "No additional info"

            # Insert the product data into the database
            cursor.execute('''INSERT INTO products (name, price, link, additional_info) 
                              VALUES (?, ?, ?, ?)''', (name, price, link, info))
        except Exception as e:
            pass

    # Commit all insertions at once
    conn.commit()

    # Optional: Confirm data retrieval
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    print(f"\nThere are {len(rows)} products in the database.")

else:
    print(f"Failed to retrieve content. Status code: {response.status_code}")

# Close the database connection when done
conn.close()
