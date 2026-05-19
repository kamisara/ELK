from flask import Flask, jsonify
import logging
import random
import time
import json
from datetime import datetime

app = Flask(__name__)

# Configure JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "checkout-microservice",
            "message": record.getMessage(),
        }
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        return json.dumps(log_entry)

# Setup logger
logger = logging.getLogger("checkout")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Fake products
PRODUCTS = [
    {"id": "P001", "name": "Laptop", "price": 999.99},
    {"id": "P002", "name": "Phone", "price": 699.99},
    {"id": "P003", "name": "Tablet", "price": 499.99},
    {"id": "P004", "name": "Headphones", "price": 199.99},
    {"id": "P005", "name": "Smartwatch", "price": 299.99},
]

# Fake users
USERS = ["user_001", "user_002", "user_003", "user_004", "user_005"]

@app.route("/health")
def health():
    logger.info("Health check OK", extra={"extra": {"endpoint": "/health", "status": "healthy"}})
    return jsonify({"status": "healthy"})

@app.route("/checkout", methods=["GET"])
def checkout():
    user = random.choice(USERS)
    product = random.choice(PRODUCTS)
    scenario = random.choices(
        ["success", "timeout", "payment_failed", "out_of_stock"],
        weights=[60, 15, 15, 10]
    )[0]

    # Simulate processing time
    if scenario == "timeout":
        time.sleep(random.uniform(2.0, 4.0))
        logger.warning("Checkout timeout", extra={"extra": {
            "user_id": user,
            "product_id": product["id"],
            "product_name": product["name"],
            "price": product["price"],
            "scenario": "timeout",
            "latency_ms": random.randint(2000, 4000),
            "endpoint": "/checkout"
        }})
        return jsonify({
            "status": "timeout",
            "user": user,
            "product": product["name"]
        }), 408

    elif scenario == "payment_failed":
        time.sleep(random.uniform(0.1, 0.5))
        logger.error("Payment failed", extra={"extra": {
            "user_id": user,
            "product_id": product["id"],
            "product_name": product["name"],
            "price": product["price"],
            "scenario": "payment_failed",
            "latency_ms": random.randint(100, 500),
            "endpoint": "/checkout"
        }})
        return jsonify({
            "status": "payment_failed",
            "user": user,
            "product": product["name"]
        }), 402

    elif scenario == "out_of_stock":
        time.sleep(random.uniform(0.05, 0.2))
        logger.warning("Product out of stock", extra={"extra": {
            "user_id": user,
            "product_id": product["id"],
            "product_name": product["name"],
            "price": product["price"],
            "scenario": "out_of_stock",
            "latency_ms": random.randint(50, 200),
            "endpoint": "/checkout"
        }})
        return jsonify({
            "status": "out_of_stock",
            "user": user,
            "product": product["name"]
        }), 404

    else:
        time.sleep(random.uniform(0.05, 0.3))
        logger.info("Checkout successful", extra={"extra": {
            "user_id": user,
            "product_id": product["id"],
            "product_name": product["name"],
            "price": product["price"],
            "scenario": "success",
            "latency_ms": random.randint(50, 300),
            "endpoint": "/checkout"
        }})
        return jsonify({
            "status": "success",
            "user": user,
            "product": product["name"],
            "price": product["price"]
        }), 200

@app.route("/products")
def products():
    logger.info("Products listed", extra={"extra": {
        "endpoint": "/products",
        "count": len(PRODUCTS)
    }})
    return jsonify(PRODUCTS)

if __name__ == "__main__":
    logger.info("Checkout microservice starting", extra={"extra": {
        "service": "checkout-microservice",
        "version": "1.0.0"
    }})
    app.run(host="0.0.0.0", port=5000)