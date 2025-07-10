from pydantic import BaseModel
from datetime import date

class ExpenseBase(BaseModel):
    title: str
    amount: float  # ✅ Changed from int to float
    category: str
    date: date

class ExpenseCreate(ExpenseBase):
    pass

class Expense(ExpenseBase):
    id: int

    model_config = {
        "from_attributes": True  # Equivalent of orm_mode=True in Pydantic v1
    }