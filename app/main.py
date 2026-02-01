from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.db import init_db
#from app.routers.foods import router as foods_router
from app.routers import log, foods
from app.openfoodfacts import fetch_by_barcode


app = FastAPI(
    title="Count Cals",
    description="AFCD + Open Food Facts backend",
    version="0.1.0",
)

# --- Routers ---
app.include_router(foods.router)
app.include_router(log.router)

# --- Static files ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- Startup ---
@app.on_event("startup")
def startup():
    init_db()

# --- External lookups ---
@app.get("/foods/barcode/{barcode}")
def barcode_lookup(barcode: str):
    food = fetch_by_barcode(barcode)
    if not food:
        raise HTTPException(status_code=404, detail="Product not found")
    return food

# --- Health check ---
@app.get("/")
def health():
    return {"status": "ok"}
