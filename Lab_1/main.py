import socket
import ssl
from bs4 import BeautifulSoup
from functools import reduce
from datetime import datetime, timezone

MDL_TO_EUR = 0.05
EUR_TO_MDL = 20.0

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

def serialize(data):
    if isinstance(data, dict):
        serialized_str = "[D:"
        for key, value in data.items():
            serialized_str += f"{key}={serialize(value)};"
        return serialized_str.rstrip(';') + "]"

    elif isinstance(data, list):
        serialized_str = "[L:"
        for item in data:
            serialized_str += f"{serialize(item)};"
        return serialized_str.rstrip(';') + "]"

    elif isinstance(data, str):
        return f'str("{data}")'

    elif isinstance(data, int):
        return f'int({data})'

    elif isinstance(data, float):
        return f'float({data})'

    else:
        return "unknown"

def deserialize(data):
    result = []
    # Split by the delimiter used for different products
    products = data.strip('[]').split('];[')

    for product in products:
        product_dict = {}
        # Extract name
        name_part = product.split(';')[0].split('=')[1].strip('str("').strip('")')
        product_dict['name'] = name_part

        # Extract price
        price_part = product.split(';')[1].split('=')[1].strip('int()')
        product_dict['price'] = int(price_part)

        # Extract link
        link_part = product.split(';')[2].split('=')[1].strip('str("').strip('")')
        product_dict['link'] = link_part

        # Extract price with interest
        price_with_interest_part = product.split(';')[3].split('=')[1].strip('int()')
        product_dict['price_with_interest'] = int(price_with_interest_part)

        result.append(product_dict)

    return result

def serialize_to_json(data):
    if isinstance(data, list):
        json_str = "["
        for item in data:
            json_str += serialize_to_json(item) + ","
        json_str = json_str.rstrip(',') + "]"
        return json_str
    elif isinstance(data, dict):
        json_str = "{"
        for key, value in data.items():
            json_str += f'"{key}": {serialize_to_json(value)},'
        json_str = json_str.rstrip(',') + "}"
        return json_str
    elif isinstance(data, str):
        return f'"{data}"'
    elif isinstance(data, (int, float)):
        return str(data)
    else:
        return "null"

def serialize_to_xml(data):
    if isinstance(data, list):
        xml_str = "<products>"
        for item in data:
            xml_str += serialize_to_xml(item)
        xml_str += "</products>"
        return xml_str
    elif isinstance(data, dict):
        xml_str = "<product>"
        for key, value in data.items():
            xml_str += f"<{key}>{serialize_to_xml(value)}</{key}>"
        xml_str += "</product>"
        return xml_str
    elif isinstance(data, str):
        return data
    elif isinstance(data, (int, float)):
        return str(data)
    else:
        return ""

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

            # Send a second request to get additional product details
            response2 = send_http_request(host, link, use_https=True)
            if response2:
                soup2 = BeautifulSoup(response2, "html.parser")
                price2_label = soup2.find("label", class_="cursor-pointer font-semibold")
                if price2_label is not None:
                    price2 = price2_label.text.strip()
                    validated_data2 = validate_product(name, price2)
                    if validated_data2 is None:
                        continue

                    validated_data['link'] = link
                    validated_data['price_with_interest'] = validated_data2['price']
                    validated_products.append(validated_data)

                    print(f"Product: {validated_data['name']}\n"
                          f"Price: {validated_data['price']} MDL\n"
                          f"Price with interest: {validated_data2['price']} MDL\n"
                          f"Link: {link}\n")
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

    # Serialize the validated products to custom format
    custom_output = serialize(validated_products)

    # Print serialized outputs
    print("\nCustom Serialized Format:")
    print(custom_output)

    # Deserialize the custom format back to a Python object
    deserialized_data = deserialize(custom_output)
    print("\nDeserialized Data (Custom Format):")
    print(deserialized_data)

    # Serialize to JSON format
    json_output = serialize_to_json(validated_products)
    print("\nJSON Serialized Format:")
    print(json_output)

    # Serialize to XML format
    xml_output = serialize_to_xml(validated_products)
    print("\nXML Serialized Format:")
    print(xml_output)

    # Display filtered products and total price
    print("\nFiltered Products:")
    for product in final_data['filtered_products']:
        print(f"- {product['name']}: €{product['price']:.2f}")

    print(f"\nTotal Price: €{final_data['total_price']:.2f}")
    print(f"Timestamp: {final_data['timestamp']}")
else:
    print("Failed to retrieve content.")