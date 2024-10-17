import requests
from bs4 import BeautifulSoup

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


url = "https://ultra.md/category/tv-televizory"
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    print("Successfully retrieved HTML content from URL.")

    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.find_all("div", class_="product-block")

    for product in products:
        try:
            # Extract product name, price, and link
            name = product.find("a", class_="product-text").text
            price = " ".join(product.find("span", class_="text-blue text-xl font-bold dark:text-white").text.split())
            link = product.find("a", class_="product-text")["href"]

            # Validate product data (price1)
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

                    # Validate the second price (price2)
                    validated_data2 = validate_product(name, price2)
                    if validated_data2 is None:
                        print(f"Invalid price2 for product {name}. Skipping.")
                        continue

                    # Display the extracted and validated information
                    print(f"Product: {validated_data['name']}\nPrice: {validated_data['price']} MDL\nLink: {link}\nPrice with interest: {validated_data2['price']} MDL\n")
                else:
                    print(f"Price2 not found for product {name}. Skipping.")
            else:
                print(f"Failed to retrieve content for product link {link}. Status code: {response2.status_code}")

        except AttributeError:
            # Handle general attribute errors without printing the stack trace
            print(f"Failed to extract some product details for {name}. Skipping.")

else:
    print(f"Failed to retrieve content. Status code: {response.status_code}")
