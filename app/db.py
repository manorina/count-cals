import sqlite3
import os
from pathlib import Path

# not DOcker friendly ->
#BASE_DIR = Path(__file__).resolve().parent.parent
#DB_PATH = BASE_DIR / "data" / "foods.db"

# Do this instead, *must* define DB_PATH in docker-compose.yml:
DB_PATH_OS = os.getenv("DB_PATH", "/app/data/foods.db")

if not DB_PATH_OS:
    raise RuntimeError("DB_PATH environment variable not set")
    
DB_PATH = Path(DB_PATH_OS)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
    
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # foods table (already exists, but safe)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        name TEXT,
        brand TEXT,
        barcode TEXT,
        energy_kj_100g REAL,
        energy_kcal_100g REAL,
        protein_100g REAL,
        fat_100g REAL,
        carbs_100g REAL,
        fiber_100g REAL,
        last_updated TEXT
    )
    """)

    # food_log table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS food_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_id INTEGER NOT NULL,
        quantity_g REAL NOT NULL,
        consumed_at TEXT NOT NULL,
        FOREIGN KEY (food_id) REFERENCES foods(id)
    )
    """)

    conn.commit()
    conn.close()


#def init_db():
#    conn = get_connection()
#    cur = conn.cursor()
#
#    # Create food_log table if it doesn't exist
#    cur.execute("""
#    CREATE TABLE IF NOT EXISTS food_log (
#        id INTEGER PRIMARY KEY AUTOINCREMENT,
#        food_id INTEGER NOT NULL,
#        quantity_g REAL NOT NULL,
#        consumed_at TEXT NOT NULL,
#        FOREIGN KEY (food_id) REFERENCES foods(id)
#    )
#    """)
#
#    conn.commit()
#    conn.close() 
 
#def init_db():
#    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
#
#    conn = get_db()
#    cur = conn.cursor()
#
#    cur.execute("""
#    CREATE TABLE IF NOT EXISTS food_log (
#        id INTEGER PRIMARY KEY AUTOINCREMENT,
#        food_id INTEGER NOT NULL,
#        food_name TEXT NOT NULL,
#
#        quantity_input REAL NOT NULL,
#        quantity_unit TEXT NOT NULL CHECK (quantity_unit IN ('g', 'ml')),
#        quantity_g REAL NOT NULL,
#
#        consumed_at TEXT NOT NULL,
#
#        energy_kj REAL,
#        protein_g REAL,
#        fat_g REAL,
#        carbs_g REAL,
#        fiber_g REAL,
#
#        created_at TEXT NOT NULL DEFAULT (datetime('now')),
#        updated_at TEXT,
#
#        FOREIGN KEY (food_id) REFERENCES foods(id)
#    );
#    """)
#
#    conn.commit()
#    conn.close()

