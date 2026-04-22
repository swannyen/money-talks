from pydantic import BaseModel
from typing import Optional, Literal
from src.models.actions import AcceptedActions

Portfolio = Literal["Tiger", "MooMoo", "Vickers"]

Currency = Literal["SGD", "USD", "HKD", "EUR", "JPY"]  # Extend as needed

class Transaction(BaseModel):
    date: str  # accepted formats: "YYYY-MM-DD", "DD MMM YYYY"
    portfolio: Portfolio
    ticker: str
    quantity: Optional[int] = None
    currency: Currency
    action: AcceptedActions
    value: float
