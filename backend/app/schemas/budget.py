from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.schemas.category import CategoryResponse


class BudgetCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    category_id: int | None = Field(default=None, gt=0)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)


class BudgetUpdate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


class BudgetResponse(BaseModel):
    id: int
    amount: Decimal
    month: int
    year: int
    category: CategoryResponse | None
    spent: Decimal
    remaining: Decimal
    percent_used: Decimal
    status: str
    created_at: datetime
