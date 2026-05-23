"""Populate MongoDB with sample products, users, and interactions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.database import (
    get_db,
    interactions_collection,
    products_collection,
    users_collection,
)

PRODUCTS = [
    {"name": "Wireless Bluetooth Headphones", "category": "Electronics", "price": 79.99, "rating": 4.5, "review_count": 1200, "description": "Noise cancelling over-ear wireless headphones with 30h battery"},
    {"name": "USB-C Laptop Charger 65W", "category": "Electronics", "price": 45.00, "rating": 4.2, "review_count": 890, "description": "Fast charging compact adapter for laptops and phones"},
    {"name": "Smart Fitness Watch", "category": "Electronics", "price": 149.99, "rating": 4.4, "review_count": 2100, "description": "Heart rate GPS sleep tracking waterproof smartwatch"},
    {"name": "Python for Data Analysis", "category": "Books", "price": 42.00, "rating": 4.8, "review_count": 3400, "description": "Learn pandas numpy data wrangling with python"},
    {"name": "Clean Code", "category": "Books", "price": 38.50, "rating": 4.7, "review_count": 5200, "description": "Software craftsmanship readable maintainable code"},
    {"name": "The Pragmatic Programmer", "category": "Books", "price": 44.99, "rating": 4.6, "review_count": 2800, "description": "Journey to mastery tips for career developers"},
    {"name": "Nonstick Cookware Set 10pc", "category": "Home", "price": 89.99, "rating": 4.3, "review_count": 650, "description": "Durable pots pans for everyday cooking"},
    {"name": "Memory Foam Pillow", "category": "Home", "price": 34.99, "rating": 4.1, "review_count": 1100, "description": "Ergonomic neck support cooling gel pillow"},
    {"name": "Robot Vacuum Cleaner", "category": "Home", "price": 299.00, "rating": 4.0, "review_count": 980, "description": "Auto mapping smart home vacuum with app control"},
    {"name": "Yoga Mat Premium 6mm", "category": "Sports", "price": 29.99, "rating": 4.5, "review_count": 1500, "description": "Non slip eco friendly exercise yoga mat"},
    {"name": "Adjustable Dumbbells 25lb", "category": "Sports", "price": 119.00, "rating": 4.4, "review_count": 720, "description": "Home gym strength training adjustable weights"},
    {"name": "Running Shoes Men", "category": "Sports", "price": 95.00, "rating": 4.3, "review_count": 1900, "description": "Lightweight breathable road running sneakers"},
    {"name": "Cotton T-Shirt Pack", "category": "Fashion", "price": 24.99, "rating": 4.0, "review_count": 800, "description": "Soft casual crew neck tees multipack"},
    {"name": "Denim Jacket Classic", "category": "Fashion", "price": 59.99, "rating": 4.2, "review_count": 430, "description": "Vintage style blue denim outerwear"},
    {"name": "Leather Belt", "category": "Fashion", "price": 32.00, "rating": 4.1, "review_count": 290, "description": "Genuine leather dress casual belt"},
    {"name": "Vitamin C Serum", "category": "Beauty", "price": 18.99, "rating": 4.6, "review_count": 2400, "description": "Brightening anti aging skincare serum"},
    {"name": "Moisturizer SPF 30", "category": "Beauty", "price": 22.50, "rating": 4.4, "review_count": 1300, "description": "Daily face sunscreen hydrating lotion"},
    {"name": "Hair Dryer Ionic", "category": "Beauty", "price": 48.00, "rating": 4.2, "review_count": 560, "description": "Fast dry low damage professional hair dryer"},
    {"name": "Mechanical Keyboard RGB", "category": "Electronics", "price": 89.00, "rating": 4.6, "review_count": 1700, "description": "Tactile switches gaming programming keyboard"},
    {"name": "4K Webcam", "category": "Electronics", "price": 69.99, "rating": 4.3, "review_count": 940, "description": "Streaming video conference autofocus webcam"},
    {"name": "Machine Learning Yearning", "category": "Books", "price": 0.00, "rating": 4.5, "review_count": 9000, "description": "Andrew Ng free ebook ml strategy"},
    {"name": "Desk Lamp LED", "category": "Home", "price": 27.99, "rating": 4.4, "review_count": 410, "description": "Adjustable brightness study office lamp"},
    {"name": "Resistance Bands Set", "category": "Sports", "price": 19.99, "rating": 4.5, "review_count": 2200, "description": "Home workout elastic bands multiple levels"},
    {"name": "Winter Beanie Hat", "category": "Fashion", "price": 14.99, "rating": 4.0, "review_count": 350, "description": "Warm knit unisex winter hat"},
]

USERS = [
    {"user_id": "user_1", "name": "Alex (Tech lover)"},
    {"user_id": "user_2", "name": "Jordan (Fitness)"},
    {"user_id": "user_3", "name": "Sam (Bookworm)"},
]

# user_id -> list of product indices they "like"
USER_LIKES_BY_INDEX = {
    "user_1": [0, 1, 2, 18, 19],  # electronics
    "user_2": [9, 10, 11, 22],    # sports
    "user_3": [3, 4, 5, 20],      # books
}


def seed():
    db = get_db()
    db.products.drop()
    db.interactions.drop()
    db.users.drop()

    result = products_collection().insert_many(PRODUCTS)
    product_ids = [str(oid) for oid in result.inserted_ids]

    users_collection().insert_many(USERS)

    for user_id, indices in USER_LIKES_BY_INDEX.items():
        for idx in indices:
            interactions_collection().insert_one({
                "user_id": user_id,
                "product_id": product_ids[idx],
                "type": "like",
            })

    print(f"Seeded {len(product_ids)} products, {len(USERS)} users, interactions OK")
    print("Sample product IDs (first 3):", product_ids[:3])
    print("Use user_1, user_2, or user_3 in the UI for personalized recommendations.")


if __name__ == "__main__":
    seed()
