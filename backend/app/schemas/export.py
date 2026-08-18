from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.models.enums import PaymentMethod, TransactionType


class ExportFilters(BaseModel):
    from_date: date | None = None
    to_date: date | None = None
    category_id: int | None = Field(default=None, gt=0)
    type: TransactionType | None = None
    payment_method: PaymentMethod | None = None

    @model_validator(mode="after")
    def validate_range(self) -> "ExportFilters":
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("The start date must be before the end date.")
        return self
