from app.db import get_db

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        name TEXT,
        brand TEXT,
        barcode TEXT UNIQUE,
        energy_kj_100g REAL,
        energy_kcal_100g REAL,
        protein_100g REAL,
        fat_100g REAL,
        carbs_100g REAL,
        fiber_100g REAL,
        last_updated TEXT
    )
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_food_name ON foods(name)
    """)

    conn.commit()
    conn.close()
