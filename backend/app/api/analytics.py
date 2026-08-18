"""Analytics and report endpoints derived entirely from ledger records."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    CategoryAnalysisItem,
    DashboardSummary,
    FinancialMetrics,
    MonthlySummary,
    TimeAnalysisItem,
)
from app.services import analytics_service
from app.services.recurring_service import process_due_transactions

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _valid_period(month: int | None, year: int | None) -> tuple[int, int]:
    today = date.today()
    selected_month, selected_year = month or today.month, year or today.year
    if not 1 <= selected_month <= 12 or not 2000 <= selected_year <= 2100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Choose a valid month and year.")
    return selected_month, selected_year


@router.get("/summary", response_model=DashboardSummary, summary="Get live dashboard balances and selected-month budget progress")
def get_summary(
    month: int | None = None,
    year: int | None = None,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    selected_month, selected_year = _valid_period(month, year)
    process_due_transactions(session, current_user.id)
    session.commit()
    return analytics_service.dashboard_summary(session, current_user.id, selected_month, selected_year)


@router.get("/metrics", response_model=FinancialMetrics, summary="Get all-time financial metrics")
def get_metrics(
    session: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> FinancialMetrics:
    process_due_transactions(session, current_user.id)
    session.commit()
    return analytics_service.financial_metrics(session, current_user.id)


@router.get("/categories", response_model=list[CategoryAnalysisItem], summary="Analyze spending by category")
def get_category_analysis(
    from_date: date | None = None,
    to_date: date | None = None,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CategoryAnalysisItem]:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="The start date must be before the end date.")
    process_due_transactions(session, current_user.id)
    session.commit()
    return analytics_service.category_analysis(session, current_user.id, from_date, to_date)


@router.get("/monthly", response_model=list[TimeAnalysisItem], summary="Get a monthly income-versus-expense time series")
def get_monthly_analysis(
    months: int = 6,
    month: int | None = None,
    year: int | None = None,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TimeAnalysisItem]:
    if not 1 <= months <= 24:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Choose between 1 and 24 months.")
    selected_month, selected_year = _valid_period(month, year)
    process_due_transactions(session, current_user.id)
    session.commit()
    return analytics_service.monthly_timeseries(session, current_user.id, months, selected_year, selected_month)


@router.get("/monthly-summary", response_model=MonthlySummary, summary="Get an explorable financial summary for one month")
def get_monthly_summary(
    month: int | None = None,
    year: int | None = None,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MonthlySummary:
    selected_month, selected_year = _valid_period(month, year)
    process_due_transactions(session, current_user.id)
    session.commit()
    return analytics_service.monthly_summary(session, current_user.id, selected_month, selected_year)
