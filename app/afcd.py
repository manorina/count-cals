from app.db import get_db

def search_afcd(name: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM foods
        WHERE source='AFCD'
        AND name LIKE ?
        LIMIT 10
    """, (f"%{name}%",))

    results = cur.fetchall()
    conn.close()
    return results
