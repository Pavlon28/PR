import requests
from bs4 import BeautifulSoup

url = "https://ultra.md/category/tv-televizory"

# Make the GET request
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    print("Successfully retrieved HTML content.")

    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.find_all("div", class_= "product-block")
    for product in products:
        try:
            name = product.find("a", class_="product-text").text
            price = " ".join(product.find("span", class_="text-blue text-xl font-bold dark:text-white").text.split())
            link = product.find("a", class_="product-text")["href"]
            response2 = requests.get(link)
            soup2 = BeautifulSoup(response2.text, "html.parser")
            info = soup2.find("label", class_="cursor-pointer font-semibold").text.strip()
            print(f"Product: {name}\n Price: {price}\n Link: {link}\n Pret cu dobanda: {info}")
        except:
            pass
else:
    print(f"Failed to retrieve content. Status code: {response.status_code}")