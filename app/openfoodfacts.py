import requests
from datetime import datetime
from app.db import get_db

OFF_URL = "https://world.openfoodfacts.org/api/v0/product"

def fetch_by_barcode(barcode: str):
    r = requests.get(f"{OFF_URL}/{barcode}.json", timeout=10)
    r.raise_for_status()
    data = r.json()

    if data["status"] != 1:
        return None

    p = data["product"]
    n = p.get("nutriments", {})

    food = {
        "source": "OFF",
        "name": p.get("product_name"),
        "brand": p.get("brands"),
        "barcode": barcode,
        "energy_kj_100g": n.get("energy-kj_100g"),
        "energy_kcal_100g": n.get("energy-kcal_100g"),
        "protein_100g": n.get("proteins_100g"),
        "fat_100g": n.get("fat_100g"),
        "carbs_100g": n.get("carbohydrates_100g"),
        "fiber_100g": n.get("fiber_100g"),
        "last_updated": datetime.utcnow().isoformat()
    }

    cache_food(food)
    return food

def cache_food(food: dict):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO foods
        (source, name, brand, barcode, energy_kj_100g,
         energy_kcal_100g, protein_100g, fat_100g,
         carbs_100g, fiber_100g, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(food.values()))

    conn.commit()
    conn.close()
