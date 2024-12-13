import pika
import requests
import json

# Consume Messages and Forward to Webserver
def consume_and_forward(queue_name="scraper_queue", webserver_url="http://localhost:5000/products"):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    def callback(ch, method, properties, body):
        product = json.loads(body)
        print(f"Received: {product}")

        # Add missing fields if required by the webserver
        product.setdefault("additional_info", "")

        # Forward product data to the webserver
        response = requests.post(webserver_url, json=product)
        print(f"Forwarded to Webserver: {response.status_code}, {response.text}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    print("Waiting for messages...")
    channel.start_consuming()

if __name__ == "__main__":
    consume_and_forward()