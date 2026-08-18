from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import Frequency, PaymentMethod, TransactionType
from app.schemas.category import CategoryResponse


class RecurringCreate(BaseModel):
    type: TransactionType = TransactionType.EXPENSE
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    category_id: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=1000)
    payment_method: PaymentMethod
    frequency: Frequency
    start_date: date
    end_date: date | None = None

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return " ".join(value.split()) if value else None

    @model_validator(mode="after")
    def valid_dates(self) -> "RecurringCreate":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date.")
        return self


class RecurringUpdate(BaseModel):
    type: TransactionType | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    category_id: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=1000)
    payment_method: PaymentMethod | None = None
    frequency: Frequency | None = None
    start_date: date | None = None
    end_date: date | None = None
    active: bool | None = None


class RecurringResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: TransactionType
    amount: Decimal
    category_id: int
    category: CategoryResponse
    description: str | None
    payment_method: PaymentMethod
    frequency: Frequency
    start_date: date
    end_date: date | None
    next_due_date: date
    active: bool
    created_at: datetime
    updated_at: datetime
