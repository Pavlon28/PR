import requests
from bs4 import BeautifulSoup
from functools import reduce
import json
from datetime import datetime

# Function to validate data: strip whitespaces and ensure price is an integer
def validate_data(name, price):
    name = name.strip()  # Remove whitespaces
    try:
        price = int(price.replace('€', '').replace(',', '').strip())  # Convert price to integer
    except ValueError:
        price = None
    return name, price

# Function to convert prices from EUR to MDL
def convert_price(price, currency='EUR'):
    exchange_rate = 19.6 if currency == 'EUR' else 1  # Use EUR to MDL conversion rate
    return price * exchange_rate

# Step 1 & 2: Make a GET request and parse HTML content
def scrape_website(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        products = soup.find_all('div', class_='product-item')  # Adjust the class based on site structure

        scraped_data = []

        for product in products:
            name = product.find('h2', class_='product-title').text.strip()
            price = product.find('span', class_='price').text.strip()
            link = product.find('a')['href']  # Get the link to the product page
            # Validate the data
            name, price = validate_data(name, price)

            # Step 3: Scrape additional details from product link (e.g., color)
            product_page = requests.get(link)
            product_soup = BeautifulSoup(product_page.text, 'html.parser')
            color = product_soup.find('span', class_='color').text.strip() if product_soup.find('span', class_='color') else 'Unknown'

            scraped_data.append({
                'name': name,
                'price': price,
                'currency': 'EUR',
                'link': link,
                'color': color
            })

        return scraped_data
    else:
        print("Failed to retrieve the website.")
        return []

# Step 4 & 5: Process the products using map, filter, and reduce
def process_products(products):
    # Convert prices from EUR to MDL
    products = list(map(lambda p: {**p, 'price': convert_price(p['price'], p['currency'])}, products))

    # Filter products within a price range (100 to 1000 MDL)
    filtered_products = list(filter(lambda p: 100 <= p['price'] <= 1000, products))

    # Reduce to sum up the prices of filtered products
    total_price = reduce(lambda x, y: x + y, [p['price'] for p in filtered_products])

    # Attach UTC timestamp
    timestamp = datetime.utcnow().isoformat()

    return {
        'filtered_products': filtered_products,
        'total_price': total_price,
        'timestamp': timestamp
    }

# Step 6: Manual serialization to JSON and XML
def serialize_to_json(data):
    return json.dumps(data, indent=4)

def serialize_to_xml(data):
    xml = "<products>"
    for product in data['filtered_products']:
        xml += f"<product><name>{product['name']}</name><price>{product['price']}</price><color>{product['color']}</color></product>"
    xml += f"<total_price>{data['total_price']}</total_price>"
    xml += f"<timestamp>{data['timestamp']}</timestamp>"
    xml += "</products>"
    return xml

# Main execution
url = "https://darwin.md"  # Replace with the actual site URL
products = scrape_website(url)
if products:
    processed_data = process_products(products)

    # Serialize data to JSON and XML
    json_output = serialize_to_json(processed_data)
    xml_output = serialize_to_xml(processed_data)

    print("JSON Serialized Data:")
    print(json_output)

    print("\nXML Serialized Data:")
    print(xml_output)