import socket
import ssl
from bs4 import BeautifulSoup
from functools import reduce
from datetime import datetime, timezone

MDL_TO_EUR = 0.05  # Example conversion rate
EUR_TO_MDL = 20.0  # Example conversion rate

def send_http_request(host, path, use_https=True):
    port = 443 if use_https else 80
    request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if use_https:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # Skip SSL verification

            with context.wrap_socket(s, server_hostname=host) as ssock:
                ssock.connect((host, port))
                ssock.sendall(request.encode())
                response = b""
                while True:
                    data = ssock.recv(4096)
                    if not data:
                        break
                    response += data
        else:
            s.connect((host, port))
            s.sendall(request.encode())
            response = b""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                response += data

    return response.decode()

def get_html_body(response):
    if "\r\n\r\n" not in response:
        return None
    headers, body = response.split("\r\n\r\n", 1)
    if "200 OK" not in headers:
        return None
    return body

def validate_product(name, price):
    name = name.strip()
    cleaned_price = price.replace(" ", "").replace("lei", "")
    try:
        price_int = int(cleaned_price)
    except ValueError:
        return None
    return {"name": name, "price": price_int}

def convert_price(price, to_currency='EUR'):
    if to_currency == 'EUR':
        return price * MDL_TO_EUR
    else:
        return int(price / MDL_TO_EUR)

def price_filter(product, min_price, max_price):
    return min_price <= product['price'] <= max_price

# JSON Serialization
def serialize_to_json(data):
    import json
    return json.dumps(data)

# XML Serialization
def serialize_to_xml(data):
    xml_str = "<products>"

    for item in data:
        xml_str += f'<product><name>{item["name"]}</name><price>{item["price"]}</price></product>'

    xml_str += "</products>"

    return xml_str

# Custom Serialization
def serialize_to_custom_format(data):
    serialized_str = "Products:\n"

    for item in data:
        serialized_str += "  Product:\n"
        serialized_str += f"    -product title: {item['name']}\n"
        serialized_str += f"    -price: {item['price']} MDL\n"

        # Calculate price with interest (e.g., adding 20% interest)
        price_with_interest = int(item['price'] * 1.20)
        serialized_str += f"    -price with interest: {price_with_interest} MDL\n"

        # Include the product link
        serialized_str += f"    -link: {item['link']}\n"

    return serialized_str

# Custom Deserialization
def deserialize_from_custom_format(serialized_str):
    lines = serialized_str.strip().split("\n")
    products = []
    current_product = {}

    for line in lines:
        line = line.strip()

        if line.startswith("Product:"):
            if current_product:  # If a product was being parsed, save it
                products.append(current_product)
            current_product = {}

        elif line.startswith("-product title:"):
            current_product['name'] = line.split(": ", 1)[1].strip()

        elif line.startswith("-price:"):
            current_product['price'] = int(line.split(": ", 1)[1].strip().replace("MDL", "").strip())

        elif line.startswith("-price with interest:"):
            current_product['price_with_interest'] = int(line.split(": ", 1)[1].strip().replace("MDL", "").strip())

        elif line.startswith("-link:"):
            current_product['link'] = line.split(": ", 1)[1].strip()

    # Append the last product if it exists
    if current_product:
        products.append(current_product)

    return products

# Send the raw request to the site
host = "ultra.md"
path = "/category/tv-televizory"
raw_response = send_http_request(host, path, use_https=True)

html_content = get_html_body(raw_response)

if html_content:
    soup = BeautifulSoup(html_content, "html.parser")
    products = soup.find_all("div", class_="product-block")

    validated_products = []

    # First display all products with their details
    print("All Products:")
    for product in products:
        try:
            name = product.find("a", class_="product-text").text
            price = " ".join(product.find("span", class_="text-blue text-xl font-bold dark:text-white").text.split())
            link = product.find("a", class_="product-text")["href"]

            validated_data = validate_product(name, price)
            if validated_data is None:
                continue

            response2 = send_http_request(host, link, use_https=True)
            if response2:
                soup2 = BeautifulSoup(response2, "html.parser")
                price2_label = soup2.find("label", class_="cursor-pointer font-semibold")
                if price2_label is not None:
                    price2 = price2_label.text.strip()
                    validated_data2 = validate_product(name, price2)
                    if validated_data2 is None:
                        continue

                    # Add link and price with interest to validated data
                    validated_data['link'] = link
                    validated_data['price_with_interest'] = validated_data2['price']
                    validated_products.append(validated_data)

                    # Print product details
                    print(f"Product: {validated_data['name']}\nPrice: {validated_data['price']} MDL\nPrice with interest: {validated_data2['price']} MDL\nLink: {link}\n")
        except AttributeError:
            continue

    # Filter and display the products within the price range
    min_price = 100
    max_price = 1000

    products_in_eur = list(map(lambda p: {**p, 'price': convert_price(p['price'], 'EUR')}, validated_products))
    filtered_products = list(filter(lambda p: price_filter(p, min_price, max_price), products_in_eur))
    total_price = reduce((lambda acc, p: acc + p['price']), filtered_products, 0)

    final_data = {
        "filtered_products": filtered_products,
        "total_price": total_price,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Serialize to JSON, XML, and custom format
    json_output = serialize_to_json(filtered_products)
    xml_output = serialize_to_xml(filtered_products)
    custom_output = serialize_to_custom_format(validated_products)

    # Print serialized outputs
    print("\nSerialized JSON:")
    print(json_output)

    print("\nSerialized XML:")
    print(xml_output)

    print("\nCustom Serialized Format:")
    print(custom_output)

    # Deserialize the custom format back to Python object
    deserialized_data = deserialize_from_custom_format(custom_output)
    print("\nDeserialized Data (Custom Format):")
    print(deserialized_data)

    # Display filtered products and total price
    print("\nFiltered Products:")
    for product in final_data['filtered_products']:
        print(f"- {product['name']}: €{product['price']:.2f}")

    print(f"\nTotal Price: €{final_data['total_price']:.2f}")
    print(f"Timestamp: {final_data['timestamp']}")
else:
    print("Failed to retrieve content.")