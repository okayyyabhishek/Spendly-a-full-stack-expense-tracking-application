"""Recurring schedule CRUD and automatic due-date materialization."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.recurring_transaction import RecurringTransaction
from app.models.user import User
from app.schemas.recurring import RecurringCreate, RecurringResponse, RecurringUpdate
from app.services.ledger_service import get_owned_category
from app.services.recurring_service import process_due_transactions

router = APIRouter(prefix="/recurring", tags=["recurring transactions"])


def _owned_schedule(session: Session, user_id: int, schedule_id: int) -> RecurringTransaction:
    schedule = session.scalar(
        select(RecurringTransaction)
        .options(selectinload(RecurringTransaction.category))
        .where(RecurringTransaction.id == schedule_id, RecurringTransaction.user_id == user_id)
    )
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction not found.")
    return schedule


@router.get("", response_model=list[RecurringResponse], summary="List schedules after processing transactions due today")
def list_recurring(
    session: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[RecurringTransaction]:
    process_due_transactions(session, current_user.id)
    session.commit()
    return list(
        session.scalars(
            select(RecurringTransaction)
            .options(selectinload(RecurringTransaction.category))
            .where(RecurringTransaction.user_id == current_user.id)
            .order_by(RecurringTransaction.active.desc(), RecurringTransaction.next_due_date)
        )
    )


@router.post("", response_model=RecurringResponse, status_code=status.HTTP_201_CREATED, summary="Create a recurring schedule")
def create_recurring(
    payload: RecurringCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecurringTransaction:
    get_owned_category(session, current_user.id, payload.category_id, payload.type)
    schedule = RecurringTransaction(
        user_id=current_user.id,
        next_due_date=payload.start_date,
        active=True,
        **payload.model_dump(),
    )
    session.add(schedule)
    session.flush()
    process_due_transactions(session, current_user.id)
    session.commit()
    session.refresh(schedule, attribute_names=["category"])
    return schedule


@router.put("/{schedule_id}", response_model=RecurringResponse, summary="Update a recurring schedule")
def update_recurring(
    schedule_id: int,
    payload: RecurringUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecurringTransaction:
    schedule = _owned_schedule(session, current_user.id, schedule_id)
    updates = payload.model_dump(exclude_unset=True)
    resulting_type = updates.get("type", schedule.type)
    resulting_category_id = updates.get("category_id", schedule.category_id)
    resulting_start = updates.get("start_date", schedule.start_date)
    resulting_end = updates.get("end_date", schedule.end_date)
    if resulting_end is not None and resulting_end < resulting_start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="End date cannot be before start date.")
    get_owned_category(session, current_user.id, resulting_category_id, resulting_type)
    for field, value in updates.items():
        setattr(schedule, field, value)
    if "start_date" in updates and schedule.next_due_date < schedule.start_date:
        schedule.next_due_date = schedule.start_date
    if schedule.end_date is not None and schedule.next_due_date > schedule.end_date:
        schedule.active = False
    process_due_transactions(session, current_user.id)
    session.commit()
    session.refresh(schedule, attribute_names=["category"])
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Stop and remove a recurring schedule")
def delete_recurring(
    schedule_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    schedule = _owned_schedule(session, current_user.id, schedule_id)
    session.delete(schedule)
    session.commit()


@router.post("/process-due", summary="Materialize any recurring entries that are due")
def process_due(
    session: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict[str, int]:
    created = process_due_transactions(session, current_user.id)
    session.commit()
    return {"created": created}
