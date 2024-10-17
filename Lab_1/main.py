import requests
from bs4 import BeautifulSoup
from functools import reduce
from datetime import datetime, timezone

# Conversion rates
MDL_TO_EUR = 0.05  # Example conversion rate
EUR_TO_MDL = 20.0  # Example conversion rate

def validate_product(name, price):
    # Clean up name
    name = name.strip()

    # Remove spaces and the 'lei' currency symbol
    cleaned_price = price.replace(" ", "").replace("lei", "")

    try:
        # Convert cleaned price to integer
        price_int = int(cleaned_price)
    except ValueError:
        print(f"Invalid price format: {price}")
        return None  # Return None if price is not valid

    return {"name": name, "price": price_int}

def convert_price(price, to_currency='EUR'):
    if to_currency == 'EUR':
        return price * MDL_TO_EUR  # Convert MDL to EUR
    else:
        return int(price / MDL_TO_EUR)  # Convert EUR to MDL

def price_filter(product, min_price, max_price):
    return min_price <= product['price'] <= max_price

url = "https://ultra.md/category/tv-televizory"
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    print("Successfully retrieved HTML content from URL.")

    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.find_all("div", class_="product-block")

    validated_products = []

    for product in products:
        try:
            # Extract product name, price, and link
            name = product.find("a", class_="product-text").text
            price = " ".join(product.find("span", class_="text-blue text-xl font-bold dark:text-white").text.split())
            link = product.find("a", class_="product-text")["href"]

            # Validate product data
            validated_data = validate_product(name, price)
            if validated_data is None:
                print(f"Invalid price for product {name}. Skipping.")
                continue

            # Scrape additional product info from the product page
            response2 = requests.get(link)
            if response2.status_code == 200:
                soup2 = BeautifulSoup(response2.text, "html.parser")

                # Safely find price2 and check if it exists
                price2_label = soup2.find("label", class_="cursor-pointer font-semibold")
                if price2_label is not None:
                    price2 = price2_label.text.strip()

                    # Validate the second price
                    validated_data2 = validate_product(name, price2)
                    if validated_data2 is None:
                        print(f"Invalid price2 for product {name}. Skipping.")
                        continue

                    # Append validated product data
                    validated_products.append(validated_data)

                    # Print original output with link
                    print(f"Product: {validated_data['name']}\nPrice: {validated_data['price']} MDL\nPrice with interest: {validated_data2['price']} MDL\nLink: {link}\n")

                else:
                    print(f"Price2 not found for product {name}. Skipping.")
            else:
                print(f"Failed to retrieve content for product link {link}. Status code: {response2.status_code}")

        except AttributeError:
            continue

    # Processing the products using map, filter, and reduce
    min_price = 100  # Set your minimum price
    max_price = 1000  # Set your maximum price

    # Map: Convert prices to EUR
    products_in_eur = list(map(lambda p: {**p, 'price': convert_price(p['price'], 'EUR')}, validated_products))

    # Filter: Keep products within the price range
    filtered_products = list(filter(lambda p: price_filter(p, min_price, max_price), products_in_eur))

    # Reduce: Sum up the prices of the filtered products
    total_price = reduce(lambda acc, p: acc + p['price'], filtered_products, 0)

    # Prepare the final data structure
    final_data = {
        "filtered_products": filtered_products,
        "total_price": total_price,
        "timestamp": datetime.now(timezone.utc).isoformat()  # UTC timestamp
    }

    # Pretty print the final result
    print("\nFiltered Products:")
    for product in final_data['filtered_products']:
        print(f"- {product['name']}: €{product['price']:.2f}")

    print(f"\nTotal Price: €{final_data['total_price']:.2f}")
    print(f"Timestamp: {final_data['timestamp']}")

else:
    print(f"Failed to retrieve content. Status code: {response.status_code}")
