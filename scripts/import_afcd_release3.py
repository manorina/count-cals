#!/usr/bin/env python3

# use sys module for temp bug fixing
#import sys 
import re
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

#BASE_DIR = Path(__file__).resolve().parent.parent
#DB_PATH = BASE_DIR / "data" / "foods.db"

#AFCD_DIR = Path.home() / "count-cals" / "AFCD_data"
AFCD_DIR = Path("/data/AFCD_data")


FOOD_DETAILS_FILE = AFCD_DIR / "AFCD Release 3 - Food Details.xlsx"
NUTRIENTS_FILE = AFCD_DIR / "AFCD Release 3 - Nutrient profiles.xlsx"

def main():
    for f in (FOOD_DETAILS_FILE, NUTRIENTS_FILE):
        if not f.exists():
            raise FileNotFoundError(f"Missing file: {f}")

    print("Loading Food Details…")
    food_df = pd.read_excel(
        FOOD_DETAILS_FILE,
        sheet_name="Food details",
        header=2  # row 3 contains column names
    )

    print("Loading Nutrient Profiles (per 100g)…")
    nutr_df = pd.read_excel(
        NUTRIENTS_FILE,
        sheet_name="All solids & liquids per 100 g",
        header=2
    )

    # Inspect columns (first run sanity check)
    print("\nFood Details columns:")
    print(food_df.columns.tolist())

    print("\nNutrient Profile columns:")
    print(nutr_df.columns.tolist())

    # ---- Normalise column names ----
    #food_df = food_df.rename(columns={
    #    "Public food key": "food_key",
    #    "Food Name": "name",
    #})
    def normalise_columns(df):
    #    return (
    #        df.rename(columns=lambda c: c.replace("\n", "").strip())
    #    )
        return df.rename(
            columns=lambda c: re.sub(r"\s+", " ", c).strip()
        )

    food_df = normalise_columns(food_df)
    nutr_df = normalise_columns(nutr_df)

    # --- temp code to inspect: REMOVE ME"
    #print("\nRAW nutrient columns:")
    #for c in nutr_df.columns:
    #    print(repr(c))
    #
    #user_input = input("Press 'q' to quit: ")

    #if user_input.lower() == 'q':
    #    print("Quitting the program.")
    #    sys.exit()
    #else:
    #    print(f"You pressed '{user_input}', continuing the program.")

    # --- end temp code - BJC

    #nutr_df = nutr_df.rename(columns={
    #    "Public food key": "food_key",
    #    "Energy, without dietary fibre (kJ)": "energy_kj_100g",
    #    "Protein (g)": "protein_100g",
    #    "Fat, total (g)": "fat_100g",
    #    "Available carbohydrate, without sugar alcohols (g)": "carbs_100g",
    #    "Dietary fibre (g)": "fiber_100g",
    #})
    food_df = food_df.rename(columns={
        "Public food key": "food_key",
        "Public Food Key": "food_key",  # defensive
        "Food Name": "name",
    })

    nutr_df = nutr_df.rename(columns={
        "Public Food Key": "food_key",

        # Energy (handle comma vs no comma)
        "Energy, without dietary fibre, equated (kJ)": "energy_kj_100g",
        "Energy without dietary fibre, equated (kJ)": "energy_kj_100g",

        "Protein (g)": "protein_100g",
        "Fat, total (g)": "fat_100g",

        "Available carbohydrate, without sugar alcohols (g)": "carbs_100g",

        "Total dietary fibre (g)": "fiber_100g",
    })


    # Keep only what we need
    #nutr_df = nutr_df[
    #    [
    #        "food_key",
    #        "energy_kj_100g",
    #        "protein_100g",
    #        "fat_100g",
    #        "carbs_100g",
    #        "fiber_100g",
    #    ]
    #]
    required_cols = [
        "food_key",
        "energy_kj_100g",
        "protein_100g",
        "fat_100g",
        "carbs_100g",
        "fiber_100g",
    ]
    #print("Columns after renaming:")
    #print(nutr_df.columns.tolist())
    #sys.exit(1)

    missing = [c for c in required_cols if c not in nutr_df.columns]
    if missing:
        raise RuntimeError(f"AFCD nutrient columns missing: {missing}")

    nutr_df = nutr_df[required_cols]

    # ---- Merge ----
    df = food_df[["food_key", "name"]].merge(
        nutr_df,
        on="food_key",
        how="inner"
    )

    # ---- Derived & fixed fields ----
    df["energy_kcal_100g"] = df["energy_kj_100g"] / 4.184
    df["source"] = "AFCD"
    df["brand"] = None
    df["barcode"] = None
    df["last_updated"] = datetime.utcnow().isoformat()

    # Drop foods with no energy
    df = df.dropna(subset=["energy_kj_100g"])

    print(f"\nPrepared {len(df)} AFCD foods")

    # ---- Insert into SQLite ----
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Clear previous AFCD data only
    cur.execute("DELETE FROM foods WHERE source='AFCD'")

    insert_sql = """
    INSERT INTO foods
    (source, name, brand, barcode,
     energy_kj_100g, energy_kcal_100g,
     protein_100g, fat_100g,
     carbs_100g, fiber_100g,
     last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    rows = df[
        [
            "source", "name", "brand", "barcode",
            "energy_kj_100g", "energy_kcal_100g",
            "protein_100g", "fat_100g",
            "carbs_100g", "fiber_100g",
            "last_updated",
        ]
    ].itertuples(index=False, name=None)

    cur.executemany(insert_sql, rows)
    conn.commit()
    conn.close()

    print("AFCD Release 3 import complete ✅")

if __name__ == "__main__":
    main()
