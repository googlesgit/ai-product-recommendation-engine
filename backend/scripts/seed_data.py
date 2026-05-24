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
    {"name": "Countertop Microwave Oven 900W", "category": "Home", "price": 129.99, "rating": 4.4, "review_count": 2100, "description": "Compact micro oven microwave for kitchen reheating defrosting and quick meals", "tags": ["kitchen", "appliance", "micro oven"]},
    {"name": "Digital Air Fryer 5 Quart", "category": "Home", "price": 79.99, "rating": 4.5, "review_count": 3200, "description": "Healthy oil-free frying roasting and baking countertop air fryer"},
    {"name": "Programmable Coffee Maker 12 Cup", "category": "Home", "price": 49.99, "rating": 4.3, "review_count": 1800, "description": "Brew strength control timer glass carafe morning coffee machine"},
    {"name": "High Speed Blender 1500W", "category": "Home", "price": 89.00, "rating": 4.6, "review_count": 1400, "description": "Smoothies ice crush soup puree professional kitchen blender"},
    {"name": "Wireless Gaming Mouse", "category": "Electronics", "price": 59.99, "rating": 4.5, "review_count": 2600, "description": "Low latency RGB ergonomic mouse for PC gaming"},
    {"name": "10 inch Android Tablet", "category": "Electronics", "price": 199.99, "rating": 4.2, "review_count": 890, "description": "WiFi tablet for streaming reading and casual games"},
    {"name": "Apple iPhone 15 128GB", "category": "Electronics", "price": 799.00, "rating": 4.7, "review_count": 8500, "description": "Apple iPhone 15 smartphone 5G dual camera iOS mobile phone", "tags": ["iphone", "apple", "smartphone", "phone"]},
    {"name": "iPhone 15 Silicone Case", "category": "Electronics", "price": 49.00, "rating": 4.5, "review_count": 2100, "description": "Protective silicone case for Apple iPhone 15 and iPhone 15 Pro", "tags": ["iphone", "accessory", "phone"]},
    {"name": "Samsung Galaxy S24 256GB", "category": "Electronics", "price": 749.99, "rating": 4.6, "review_count": 4200, "description": "Samsung Galaxy android smartphone 5G AI camera mobile phone", "tags": ["samsung", "smartphone", "android", "phone"]},
    {"name": "True Wireless Earbuds ANC", "category": "Electronics", "price": 99.99, "rating": 4.6, "review_count": 4100, "description": "Active noise cancelling earbuds with charging case"},
    {"name": "Electric Standing Desk", "category": "Home", "price": 349.00, "rating": 4.4, "review_count": 720, "description": "Height adjustable sit stand desk home office"},
    {"name": "Ergonomic Office Chair", "category": "Home", "price": 279.00, "rating": 4.3, "review_count": 1100, "description": "Lumbar support mesh chair for long work sessions"},
    {"name": "Ceramic Plant Pot Set 3pc", "category": "Home", "price": 32.99, "rating": 4.5, "review_count": 540, "description": "Modern indoor planters for succulents and herbs"},
    {"name": "Skincare Essentials Gift Set", "category": "Beauty", "price": 45.00, "rating": 4.7, "review_count": 1900, "description": "Cleanser serum moisturizer bundle for daily routine"},
    {"name": "Face Sunscreen SPF 50", "category": "Beauty", "price": 16.99, "rating": 4.5, "review_count": 2800, "description": "Lightweight non greasy UV protection daily wear"},
    {"name": "Hiking Backpack 40L Waterproof", "category": "Sports", "price": 74.99, "rating": 4.6, "review_count": 1500, "description": "Trail camping backpack with rain cover and hydration sleeve"},
    {"name": "Pro Tennis Racket Carbon", "category": "Sports", "price": 129.00, "rating": 4.4, "review_count": 380, "description": "Lightweight control racket for intermediate players"},
    {"name": "Women's Running Sneakers", "category": "Sports", "price": 88.00, "rating": 4.5, "review_count": 2200, "description": "Cushioned road running shoes breathable mesh upper"},
    {"name": "Floral Summer Midi Dress", "category": "Fashion", "price": 54.00, "rating": 4.3, "review_count": 620, "description": "Casual lightweight dress for warm weather"},
    {"name": "Polarized UV Sunglasses", "category": "Fashion", "price": 28.00, "rating": 4.4, "review_count": 980, "description": "Glare reduction driving outdoor sports eyewear"},
    {"name": "Introduction to Algorithms 4th Ed", "category": "Books", "price": 89.99, "rating": 4.8, "review_count": 6100, "description": "CLRS classic computer science algorithms textbook"},
    {"name": "Deep Learning with Python 2nd Ed", "category": "Books", "price": 49.99, "rating": 4.7, "review_count": 2900, "description": "Keras tensorflow practical neural networks guide"},
    {"name": "Smart Home Speaker Voice Assistant", "category": "Electronics", "price": 49.99, "rating": 4.2, "review_count": 5000, "description": "Music podcasts smart home control hands free speaker"},
    {"name": "Stainless Steel Water Bottle 32oz", "category": "Sports", "price": 24.99, "rating": 4.6, "review_count": 3300, "description": "Insulated leak proof bottle gym office travel"},
    {"name": "Electric Kettle Temperature Control", "category": "Home", "price": 39.99, "rating": 4.5, "review_count": 1700, "description": "Fast boil tea coffee kitchen electric kettle"},
    {"name": "Men's Oxford Dress Shoes", "category": "Fashion", "price": 79.00, "rating": 4.1, "review_count": 410, "description": "Leather formal shoes business interview office"},
    {"name": "Running Shorts Quick Dry", "category": "Sports", "price": 26.99, "rating": 4.4, "review_count": 1250, "description": "Lightweight athletic shorts with liner for training"},
]

USERS = [
    {"user_id": "user_1", "name": "Alex (Tech lover)", "type": "demo"},
    {"user_id": "user_2", "name": "Jordan (Fitness)", "type": "demo"},
    {"user_id": "user_3", "name": "Sam (Bookworm)", "type": "demo"},
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
