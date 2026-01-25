# app/routers/log.py

from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.db import get_db
from app.schemas import FoodLogCreate, FoodLogOut

router = APIRouter(prefix="/log", tags=["log"])

@router.post("/add", response_model=FoodLogOut)
def add_food_to_log(entry: FoodLogCreate):
    conn = get_db()
    cur = conn.cursor()

    # ---- Fetch food ----
    cur.execute("""
        SELECT id, name,
               energy_kj_100g,
               protein_100g,
               fat_100g,
               carbs_100g,
               fiber_100g
        FROM foods
        WHERE id = ?
    """, (entry.food_id,))

    food = cur.fetchone()
    if not food:
        conn.close()
        raise HTTPException(status_code=404, detail="Food not found")

    # ---- Quantity handling ----
    if entry.unit not in ("g", "ml"):
        conn.close()
        raise HTTPException(status_code=400, detail="Unit must be 'g' or 'ml'")

    quantity_g = entry.quantity  # assume 1 ml ≈ 1 g for now

    factor = quantity_g / 100.0

    # ---- Nutrient scaling ----
    energy_kj = food["energy_kj_100g"] * factor
    protein_g = food["protein_100g"] * factor
    fat_g = food["fat_100g"] * factor
    carbs_g = food["carbs_100g"] * factor
    fiber_g = food["fiber_100g"] * factor

    consumed_at = entry.consumed_at or datetime.utcnow()

    # ---- Insert log row ----
    cur.execute("""
        INSERT INTO food_log (
            food_id, food_name,
            quantity_input, quantity_unit, quantity_g,
            consumed_at,
            energy_kj, protein_g, fat_g, carbs_g, fiber_g
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        food["id"], food["name"],
        entry.quantity, entry.unit, quantity_g,
        consumed_at.isoformat(),
        energy_kj, protein_g, fat_g, carbs_g, fiber_g
    ))

    log_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": log_id,
        "food_id": food["id"],
        "food_name": food["name"],
        "quantity_input": entry.quantity,
        "quantity_unit": entry.unit,
        "quantity_g": quantity_g,
        "consumed_at": consumed_at,
        "energy_kj": energy_kj,
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g,
        "fiber_g": fiber_g,
    }

