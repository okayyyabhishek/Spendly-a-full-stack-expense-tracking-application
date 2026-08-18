from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationKind


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: NotificationKind
    title: str
    body: str | None
    is_read: bool
    created_at: datetime


class NotificationPage(BaseModel):
    items: list[NotificationResponse]
    unread_count: int
