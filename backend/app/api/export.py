"""Download user-owned transaction data as CSV or a polished PDF report."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.export import ExportFilters
from app.services.export_service import as_csv, as_pdf, filtered_transactions

router = APIRouter(prefix="/export", tags=["exports"])


@router.get("/csv", summary="Export filtered transactions as CSV")
def export_csv(
    filters: ExportFilters = Depends(),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    records = filtered_transactions(session, current_user.id, filters)
    return Response(
        content=as_csv(records),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="spendly-transactions.csv"'},
    )


@router.get("/pdf", summary="Export filtered transactions and summary as PDF")
def export_pdf(
    filters: ExportFilters = Depends(),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    records = filtered_transactions(session, current_user.id, filters)
    return Response(
        content=as_pdf(records),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="spendly-report.pdf"'},
    )
