import requests
from bs4 import BeautifulSoup

# URL of the website
url = 'https://nlcollection.md/'

# Headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
}


# Function to validate product price
def validate_price(price_text):
    try:
        # Remove any non-digit characters and check if it is a valid number
        cleaned_price = ''.join(filter(str.isdigit, price_text))
        return int(cleaned_price) > 0  # Ensure price is greater than zero
    except ValueError:
        return False


# Function to validate product article
def validate_article(article_text):
    # Ensure the article is not empty and contains at least one alphanumeric character
    return bool(article_text and article_text.strip() and any(char.isalnum() for char in article_text))


# Send GET request with headers
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    print("Request successful!")
    html_content = response.text

    # Step 1: Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Step 2: Find all product elements
    products = soup.find_all('div', class_='product')

    # Step 3: Extract product details and validate them
    for product in products:
        # Extract the product article (identifier/name)
        article = product.find('div', class_='product__article')
        article_text = article.get_text(strip=True) if article else None

        # Extract the product price
        price = product.find('div', class_='product__price__current')
        price_text = price.get_text(strip=True) if price else None

        # Extract the product link
        link = product.find('a', class_='product__link')
        product_link = f"https://nlcollection.md{link['href']}" if link else "No link found"

        # Extract the image URL
        image = product.find('img', class_='product__image')
        image_url = f"https://nlcollection.md{image['src']}" if image else "No image found"

        # Extract flags (e.g., "New")
        flags = product.find('div', class_='product__flags')
        flag_text = flags.get_text(strip=True) if flags else "No flags found"

        # Extract brand
        brand = product.find('div', class_='product__brand')
        brand_text = brand.get_text(strip=True) if brand else "No brand available"

        # ---- Validation Checks ----
        if not validate_article(article_text):
            print(f"Invalid product article: {article_text}. Skipping this product.")
            continue  # Skip this product if the article is invalid

        if not price_text or not validate_price(price_text):
            print(f"Invalid product price: {price_text}. Skipping this product.")
            continue  # Skip this product if the price is invalid

        # If both validations pass, we can store or print the data
        print(f"Product Article: {article_text}")
        print(f"Price: {price_text}")
        print(f"Link: {product_link}")
        print(f"Image URL: {image_url}")
        print(f"Flags: {flag_text}")
        print(f"Brand: {brand_text}")
        print("=" * 40)

else:
    print(f"Failed to retrieve content. Status code: {response.status_code}")