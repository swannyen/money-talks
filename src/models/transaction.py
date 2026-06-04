from typing import Optional

from pydantic import BaseModel, field_validator

from src.config import get_currencies, get_portfolios
from src.models.actions import AcceptedActions


class Transaction(BaseModel):
    date: str  # accepted formats: "YYYY-MM-DD", "DD MMM YYYY"
    portfolio: str
    ticker: str
    quantity: Optional[int] = None
    currency: str
    action: AcceptedActions
    value: float

    @field_validator("portfolio")
    @classmethod
    def validate_portfolio(cls, value: str) -> str:
        allowed = get_portfolios()
        if value not in allowed:
            raise ValueError(f"Portfolio must be one of: {', '.join(allowed)}")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        allowed = get_currencies()
        normalized = value.strip().upper()
        if normalized not in allowed:
            raise ValueError(f"Currency must be one of: {', '.join(allowed)}")
        return normalized
