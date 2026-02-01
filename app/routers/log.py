from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from datetime import datetime, date
from app.db import get_connection
import sqlite3
import os

from app.templates import templates

router = APIRouter()
DB_PATH = os.getenv("DB_PATH", "/app/data/foods.db")

# ----  api AND form now use this insert_food_log() ----

def insert_food_log(food_id: int, quantity: float, unit: str) -> int:
    #conn = sqlite3.connect(DB_PATH)
    #conn.row_factory = sqlite3.Row
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM foods WHERE id = ?", (food_id,))
    food = cur.fetchone()
    if not food:
        conn.close()
        raise HTTPException(status_code=404, detail="Food not found")

    quantity_g = quantity
    if unit.lower() == "ml":
        quantity_g = quantity  # density logic later

    consumed_at = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT INTO food_log (food_id, quantity_g, consumed_at)
        VALUES (?, ?, ?)
        """,
        (food_id, quantity_g, consumed_at)
    )

    log_id = cur.lastrowid
    conn.commit()
    conn.close()
    return log_id

# --- class definition for api/log/add
class LogEntryIn(BaseModel):
    food_id: int
    quantity: float
    unit: str = "g"

@router.post("/api/log/add")
def api_add_food(entry: LogEntryIn):
    log_id = insert_food_log(entry.food_id, entry.quantity, entry.unit)
    return {"id": log_id, "status": "ok"}

# ---
@router.get("/log/add", response_class=HTMLResponse)
def add_food_form(request: Request):
    return templates.TemplateResponse(
        "log_add.html",
        {"request": request}
    )
  
# ---
@router.post("/log/add")
def add_food_form_post(
    food_id: int = Form(...),
    quantity: float = Form(...),
    unit: str = Form("g"),
):
    insert_food_log(food_id, quantity, unit)
    return RedirectResponse("/log/view", status_code=303)

# ---
@router.get("/log/view", response_class=HTMLResponse)
def view_log(request: Request, log_date: date | None = None):
    if log_date is None:
        log_date = date.today()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # --- entries ---
    cur.execute("""
        SELECT
            fl.id,
            f.name AS food_name,
            fl.quantity_g,
            fl.consumed_at,
            date(fl.consumed_at) AS logged_date,
            time(fl.consumed_at) AS logged_time,
            (f.energy_kj_100g * fl.quantity_g / 100.0) AS energy_kj,
            (f.protein_100g * fl.quantity_g / 100.0) AS protein_g,
            (f.carbs_100g * fl.quantity_g / 100.0) AS carbs_g,
            (f.fat_100g * fl.quantity_g / 100.0) AS fat_g,
            (f.fiber_100g * fl.quantity_g / 100.0) AS fiber_g
        FROM food_log fl
        JOIN foods f ON f.id = fl.food_id
        WHERE date(fl.consumed_at) = ?
        ORDER BY fl.consumed_at DESC
    """, (log_date.isoformat(),))
    rows = cur.fetchall()

    # --- totals ---
    cur.execute("""
        SELECT
            COALESCE(SUM(f.energy_kj_100g * fl.quantity_g / 100.0), 0) AS energy_kj,
            COALESCE(SUM(f.protein_100g   * fl.quantity_g / 100.0), 0) AS protein_g,
            COALESCE(SUM(f.carbs_100g     * fl.quantity_g / 100.0), 0) AS carbs_g,
            COALESCE(SUM(f.fat_100g       * fl.quantity_g / 100.0), 0) AS fat_g,
            COALESCE(SUM(f.fiber_100g     * fl.quantity_g / 100.0), 0) AS fiber_g
        FROM food_log fl
        JOIN foods f ON f.id = fl.food_id
        WHERE date(fl.consumed_at) = ?
    """, (log_date.isoformat(),))

    totals = cur.fetchone()
    conn.close()

    return templates.TemplateResponse(
        "log_list.html",
        {
            "request": request,
            "rows": rows,
            "totals": totals,
            "log_date": log_date,
        }
    )

# --- search - autocomplete:
@router.get("/api/foods/search")
def search_foods(q: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name
        FROM foods
        WHERE name LIKE ?
        ORDER BY name
        LIMIT 10
    """, (f"%{q}%",))

    rows = cur.fetchall()
    conn.close()
    return rows



