#from fastapi import APIRouter, Request
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse


from pydantic import BaseModel
from datetime import datetime, date
# already importing using app.templates
#from fastapi.templating import Jinja2Templates
from app.templates import templates

import os
import sqlite3

router = APIRouter()

DB_PATH = os.getenv("DB_PATH", "/app/data/foods.db")

# --- Request model ---
class LogEntryIn(BaseModel):
    food_id: int
    quantity: float
    unit: str = "g"  # default to grams

# --- Response model (optional) ---
class LogEntryOut(BaseModel):
    id: int
    food_name: str
    quantity_g: float
    consumed_at: str
    energy_kj: float
    protein_g: float
    fat_g: float
    carbs_g: float
    fiber_g: float

# --- GET endpoint ---

@router.get("/log/add", response_class=HTMLResponse)
def add_food_form(request: Request):
    return templates.TemplateResponse(
        "log_add.html",
        {
            "request": request,
        }
    )


# --- api log add POST endpoint ---
@router.post("/api/log/add", response_model=LogEntryOut)
def add_food_to_log(entry: LogEntryIn):
    # --- connect to DB ---
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allow dict-like access
    cur = conn.cursor()

    # --- get food info ---
    cur.execute("SELECT * FROM foods WHERE id=?", (entry.food_id,))
    food = cur.fetchone()
    if not food:
        conn.close()
        raise HTTPException(status_code=404, detail="Food not found")

    # --- convert quantity ---
    # If you want to handle liquids differently, add conversion logic here
    quantity_g = entry.quantity
    if entry.unit.lower() == "ml":
        # crude conversion: assume 1 mL = 1 g unless specified
        quantity_g = entry.quantity  # extend later if density info exists

    # --- insert into food_log ---
    consumed_at = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO food_log (food_id, quantity_g, consumed_at) VALUES (?, ?, ?)",
        (entry.food_id, quantity_g, consumed_at)
    )
    log_id = cur.lastrowid
    conn.commit()

    # --- calculate nutrients for this quantity ---
    factor = quantity_g / 100  # nutrient values are per 100g
    energy_kj = food["energy_kj_100g"] * factor
    protein_g = food["protein_100g"] * factor
    fat_g = food["fat_100g"] * factor
    carbs_g = food["carbs_100g"] * factor
    fiber_g = food["fiber_100g"] * factor

    conn.close()

    return LogEntryOut(
        id=log_id,
        food_name=food["name"],
        quantity_g=quantity_g,
        consumed_at=consumed_at,
        energy_kj=energy_kj,
        protein_g=protein_g,
        fat_g=fat_g,
        carbs_g=carbs_g,
        fiber_g=fiber_g
    )
    
# --- POST endpoint - FORM template ---

@router.post("/log/add", response_class=HTMLResponse)
def add_food_form_post(
    food_id: int = Form(...),
    quantity: float = Form(...),
    unit: str = Form("g"),
):
    # reuse your existing logic
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM foods WHERE id=?", (food_id,))
    food = cur.fetchone()
    if not food:
        conn.close()
        raise HTTPException(status_code=404, detail="Food not found")

    quantity_g = quantity
    if unit.lower() == "ml":
        quantity_g = quantity  # placeholder density logic

    consumed_at = datetime.utcnow().isoformat()

    cur.execute(
        "INSERT INTO food_log (food_id, quantity_g, consumed_at) VALUES (?, ?, ?)",
        (food_id, quantity_g, consumed_at)
    )

    conn.commit()
    conn.close()

    # redirect to log view
    return RedirectResponse(
        url="/log/view",
        status_code=303
    )

    
# ---- GET log endpoint

@router.get("/log")
def list_log_entries(log_date: date | None = None):
    if log_date is None:
        log_date = date.today()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            fl.id,
            fl.consumed_at,
            fl.quantity_g,
            f.name,
            f.energy_kj_100g,
            f.protein_100g,
            f.fat_100g,
            f.carbs_100g,
            f.fiber_100g
        FROM food_log fl
        JOIN foods f ON fl.food_id = f.id
        WHERE date(fl.consumed_at) = ?
        ORDER BY fl.consumed_at DESC
    """, (log_date.isoformat(),))

    rows = cur.fetchall()
    conn.close()

    results = []
    for r in rows:
        factor = r["quantity_g"] / 100
        results.append({
            "id": r["id"],
            "food_name": r["name"],
            "quantity_g": r["quantity_g"],
            "consumed_at": r["consumed_at"],
            "energy_kj": r["energy_kj_100g"] * factor,
            "protein_g": r["protein_100g"] * factor,
            "fat_g": r["fat_100g"] * factor,
            "carbs_g": r["carbs_100g"] * factor,
            "fiber_g": r["fiber_100g"] * factor,
        })

    return results
    
# --- jinja requests
@router.get("/log/view")
def view_log(request: Request, log_date: date | None = None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Default to today if no date provided
    if log_date is None:
        log_date = date.today()
        
# ---- entries ----
    if log_date:
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

    # ---- daily totals ----
    cur.execute("""
        SELECT
            COALESCE(SUM(f.energy_kj_100g * fl.quantity_g / 100.0), 0) AS energy_kj,
            COALESCE(SUM(f.protein_100g   * fl.quantity_g / 100.0), 0) AS protein_g,
            COALESCE(SUM(f.carbs_100g     * fl.quantity_g / 100.0), 0) AS carbs_g,
            COALESCE(SUM(f.fat_100g       * fl.quantity_g / 100.0), 0) AS fat_g,
            COALESCE(SUM(f.fiber_100g     * fl.quantity_g / 100.0), 0) AS fiber_g
        FROM food_log fl
        JOIN foods f ON f.id = fl.food_id
        WHERE fl.logged_date = ?
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
    

@router.get("/log/all")
def view_all_logs(request: Request):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            fl.id,
            f.name AS food_name,
            fl.quantity_g,
            fl.logged_date,
            fl.logged_time,
            (f.energy_kj_100g * fl.quantity_g / 100.0) AS energy_kj,
            (f.protein_100g * fl.quantity_g / 100.0) AS protein_g,
            (f.carbs_100g * fl.quantity_g / 100.0) AS carbs_g,
            (f.fat_100g * fl.quantity_g / 100.0) AS fat_g,
            (f.fiber_100g * fl.quantity_g / 100.0) AS fiber_g
        FROM food_log fl
        JOIN foods f ON f.id = fl.food_id
        ORDER BY fl.logged_date DESC, fl.logged_time DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return templates.TemplateResponse(
        "log_list.html",
        {
            "request": request,
            "rows": rows,
            "totals": None,
            "log_date": None,
        }
    )


