from sqlalchemy import Column, Integer, String, Float, Date
from .database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    amount = Column(Float, nullable=False)  # ✅ Changed from Integer to Float
    category = Column(String)
    date = Column(Date)