"""A compact, user-scoped notification center."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationPage, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationPage, summary="List recent notifications without exposing other users' alerts")
def list_notifications(
    unread_only: bool = False,
    limit: int = 30,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationPage:
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Limit must be between 1 and 100.")
    statement = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        statement = statement.where(Notification.is_read.is_(False))
    items = list(session.scalars(statement.order_by(Notification.created_at.desc()).limit(limit)))
    unread_count = session.scalar(
        select(func.count(Notification.id)).where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
    ) or 0
    return NotificationPage(items=[NotificationResponse.model_validate(item) for item in items], unread_count=unread_count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse, summary="Mark one notification as read")
def mark_read(
    notification_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Notification:
    notification = session.scalar(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    notification.is_read = True
    session.commit()
    session.refresh(notification)
    return notification


@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT, summary="Mark all of the user's notifications as read")
def mark_all_read(
    session: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> None:
    session.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    session.commit()
