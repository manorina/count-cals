from fastapi import APIRouter, Query
from typing import List, Optional
import sqlite3
from pathlib import Path

from app.schemas import FoodOut

router = APIRouter(
    prefix="/foods",
    tags=["foods"],
)

@router.get("/search", response_model=List[FoodOut])
def search_foods(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    db_path = Path(__file__).resolve().parents[2] / "data" / "foods.db"
    terms = q.lower().split()
    
    where_clauses = " AND ".join(
        ["LOWER(name) LIKE ?"] * len(terms)
    )
    
    params = [f"%{t}%" for t in terms]
    
    sql = f"""
    SELECT *
    FROM foods
    WHERE {where_clauses}
    ORDER BY name
    LIMIT 50
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()


    #cur = conn.cursor()
    #
    #cur.execute(
    #    """
    #    SELECT *
    #    FROM foods
    #    WHERE name LIKE ?
    #    ORDER BY energy_kj_100g
    #    LIMIT ?
    #    """,
    #    (f"%{q}%", limit),
    #)
    #
    #rows = cur.fetchall()
    #q_like = f"%{q}%"
    #
    #rows = conn.execute(
    #    """
    #    SELECT *
    #    FROM foods
    #    WHERE name LIKE ?
    #    ORDER BY name
    #    LIMIT 50
    #    """,
    #    (q_like,),
    #).fetchall()

    #conn.close()

    return [dict(row) for row in rows]

