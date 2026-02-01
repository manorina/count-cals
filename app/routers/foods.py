from fastapi import APIRouter, Query
from typing import List, Optional
import sqlite3
#from pathlib import Path
from app.schemas import FoodOut
from app.db import get_connection
import os

DB_PATH = os.getenv("DB_PATH", "/app/data/foods.db")


router = APIRouter(
    prefix="/foods",
    tags=["foods"],
)

@router.get("/search", response_model=List[FoodOut])
def search_foods(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    # db_path = Path(__file__).resolve().parents[2] / "data" / "foods.db"
    terms = q.lower().split()
    where_clauses = " AND ".join(
        ["LOWER(name) LIKE ?"] * len(terms)
    )
    
    params = [f"%{t}%" for t in terms]
    params.append(limit)
    
    sql = f"""
    SELECT *
    FROM foods
    WHERE {where_clauses}
    ORDER BY name
    LIMIT ?
    """
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()


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



    return [dict(row) for row in rows]

