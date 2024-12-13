import pika
import requests
from bs4 import BeautifulSoup
import json

# RabbitMQ Setup
def publish_message_to_queue(message, queue_name="scraper_queue"):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(message))
    connection.close()

# Scrape and Publish
def scrape_and_publish():
    url = "https://ultra.md/category/tv-televizory"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        products = soup.find_all("div", class_="product-block")

        for product in products:
            try:
                name = product.find("a", class_="product-text").text.strip()
                price = " ".join(product.find("span", class_="text-blue text-xl font-bold dark:text-white").text.split())
                link = product.find("a", class_="product-text")["href"]

                product_data = {
                    "name": name,
                    "price": price,
                    "link": f"https://ultra.md{link}" if not link.startswith("http") else link
                }
                publish_message_to_queue(product_data)
                print(f"Published: {product_data}")
            except AttributeError:
                print(f"Error processing product: Missing required fields.")

if __name__ == "__main__":
    scrape_and_publish()