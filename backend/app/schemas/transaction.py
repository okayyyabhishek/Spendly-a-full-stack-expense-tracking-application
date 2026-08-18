from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import PaymentMethod, TransactionType
from app.schemas.category import CategoryResponse


class TransactionCreate(BaseModel):
    type: TransactionType
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    category_id: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=1000)
    payment_method: PaymentMethod
    transaction_date: date = Field(default_factory=date.today)

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        return value or None


class TransactionUpdate(BaseModel):
    type: TransactionType | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    category_id: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=1000)
    payment_method: PaymentMethod | None = None
    transaction_date: date | None = None

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        return value or None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: TransactionType
    amount: Decimal
    category_id: int
    category: CategoryResponse
    description: str | None
    payment_method: PaymentMethod
    transaction_date: date
    recurring_transaction_id: int | None
    created_at: datetime
    updated_at: datetime


class TransactionPage(BaseModel):
    items: list[TransactionResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class TransactionFilters(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    from_date: date | None = None
    to_date: date | None = None
    category_id: int | None = Field(default=None, gt=0)
    type: TransactionType | None = None
    payment_method: PaymentMethod | None = None
    min_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    max_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    search: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validate_ranges(self) -> "TransactionFilters":
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("The start date must be before the end date.")
        if self.min_amount is not None and self.max_amount is not None and self.min_amount > self.max_amount:
            raise ValueError("Minimum amount cannot exceed maximum amount.")
        return self
