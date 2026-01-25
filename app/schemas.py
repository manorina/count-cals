from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Food(BaseModel):
    name: str
    brand: Optional[str]
    barcode: Optional[str]
    energy_kj_100g: Optional[float]
    energy_kcal_100g: Optional[float]
    protein_100g: Optional[float]
    fat_100g: Optional[float]
    carbs_100g: Optional[float]
    fiber_100g: Optional[float]
    source: str
    
class FoodOut(BaseModel):
    id: int
    name: str
    energy_kj_100g: float
    energy_kcal_100g: float
    protein_100g: Optional[float]
    fat_100g: Optional[float]
    carbs_100g: Optional[float]
    fiber_100g: Optional[float]
    source: str


# not sure these are being used.  See log.py for schemas defined inline there    
class FoodLogCreate(BaseModel):
    food_id: int
    quantity: float
    unit: str  # 'g' or 'ml'
    consumed_at: Optional[datetime] = None

class FoodLogOut(BaseModel):
    id: int
    food_id: int
    food_name: str
    quantity_input: float
    quantity_unit: str
    quantity_g: float
    consumed_at: datetime

    energy_kj: float
    protein_g: float
    fat_g: float
    carbs_g: float
    fiber_g: float
