from fastapi import FastAPI, Query, HTTPException, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles

# init_db for foods.db below
#from app.models import init_db
from app.db import init_db
from app.afcd import search_afcd
from app.openfoodfacts import fetch_by_barcode
from app.routers.foods import router as foods_router
from app.routers import log
from app.templates import templates


#router = APIRouter()
from difflib import SequenceMatcher
import sqlite3
from pathlib import Path
from typing import List
from .schemas import FoodOut


app = FastAPI(
    title="Count Cals",
    description="AFCD + Open Food Facts backend",
    version="0.1.0",
)

app.include_router(foods_router)
app.include_router(log.router)

# --- jinja2 templates
templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


#app = FastAPI(
#    title="Private Calorie Tracker",
#    description="AFCD + Open Food Facts backend",
#    version="0.1.0"
#)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "foods.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/debug/foods")
def debug_foods(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT name,
               energy_kj_100g,
               energy_kcal_100g,
               protein_100g,
               fat_100g,
               carbs_100g,
               fiber_100g
        FROM foods
        WHERE source='AFCD'
        LIMIT ?
        """,
        (limit,)
    )

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.on_event("startup")
def startup():
    init_db()

#@app.get("/foods/search")
#def search_foods(q: str):
#    results = search_afcd(q)
#    return [dict(r) for r in results]
#
#@app.get("/foods/search", response_model=List[FoodOut])
#
#def search_foods(
#    q: str = Query(..., min_length=2, description="Search term"),
#    limit: int = Query(20, ge=1, le=100),
#    source: str | None = Query(None, description="AFCD or OFF"),
#):
#    conn = get_db()
#    cur = conn.cursor()
#
#    sql = """
#        SELECT
#            id,
#            name,
#            energy_kj_100g,
#            energy_kcal_100g,
#            protein_100g,
#            fat_100g,
#            carbs_100g,
#            fiber_100g,
#            source
#        FROM foods
#        WHERE lower(name) LIKE lower(?)
#    """
#
#    params = [f"%{q}%"]
#
#    if source:
#        sql += " AND source = ?"
#        params.append(source)
#
#    sql += " ORDER BY name LIMIT ?"
#    params.append(limit)
#
#    cur.execute(sql, params)
#    rows = cur.fetchall()
#    conn.close()
#
#    return [dict(row) for row in rows]


@app.get("/foods/barcode/{barcode}")
def barcode_lookup(barcode: str):
    food = fetch_by_barcode(barcode)
    if not food:
        raise HTTPException(status_code=404, detail="Product not found")
    return food

@app.get("/")
def health():
    return {"status": "ok"}
