"""Generate CSV and compact PDF exports from persisted, filtered user transactions."""

import csv
from datetime import date
from decimal import Decimal
from html import escape
from io import BytesIO, StringIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.export import ExportFilters
from app.services.analytics_service import money


def filtered_transactions(session: Session, user_id: int, filters: ExportFilters) -> list[Transaction]:
    statement: Select[tuple[Transaction]] = (
        select(Transaction)
        .join(Category)
        .options(selectinload(Transaction.category))
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .limit(10_000)
    )
    if filters.from_date:
        statement = statement.where(Transaction.transaction_date >= filters.from_date)
    if filters.to_date:
        statement = statement.where(Transaction.transaction_date <= filters.to_date)
    if filters.category_id:
        statement = statement.where(Transaction.category_id == filters.category_id)
    if filters.type:
        statement = statement.where(Transaction.type == filters.type)
    if filters.payment_method:
        statement = statement.where(Transaction.payment_method == filters.payment_method)
    return list(session.scalars(statement))


def as_csv(records: list[Transaction]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Transaction type", "Category", "Description", "Amount", "Payment method"])
    for transaction in records:
        writer.writerow(
            [
                transaction.transaction_date.isoformat(),
                transaction.type.value.title(),
                transaction.category.name,
                transaction.description or "",
                f"{money(transaction.amount):.2f}",
                transaction.payment_method.value.replace("_", " ").title(),
            ]
        )
    return output.getvalue()


def as_pdf(records: list[Transaction], generated_on: date | None = None) -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )
    styles = getSampleStyleSheet()
    title = styles["Title"]
    title.textColor = colors.HexColor("#1B241F")
    title.fontName = "Helvetica-Bold"
    normal = styles["BodyText"]
    normal.leading = 14
    expenses = sum((money(item.amount) for item in records if item.type == TransactionType.EXPENSE), Decimal("0.00"))
    income = sum((money(item.amount) for item in records if item.type == TransactionType.INCOME), Decimal("0.00"))
    story = [
        Paragraph("Spendly financial report", title),
        Paragraph(f"Generated {escape((generated_on or date.today()).isoformat())} · {len(records)} transaction(s)", normal),
        Spacer(1, 6 * mm),
    ]
    summary_data = [
        ["Total income", "Total expenses", "Net balance"],
        [f"₹{income:.2f}", f"₹{expenses:.2f}", f"₹{income - expenses:.2f}"],
    ]
    summary = Table(summary_data, colWidths=[60 * mm, 60 * mm, 60 * mm])
    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7EEDD")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#43523D")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D8DED5")),
            ]
        )
    )
    story.extend([summary, Spacer(1, 7 * mm)])
    table_data: list[list[Paragraph]] = [
        [Paragraph("Date", normal), Paragraph("Type", normal), Paragraph("Category", normal), Paragraph("Description", normal), Paragraph("Amount", normal), Paragraph("Method", normal)]
    ]
    for item in records:
        table_data.append(
            [
                Paragraph(item.transaction_date.isoformat(), normal),
                Paragraph(escape(item.type.value.title()), normal),
                Paragraph(escape(item.category.name), normal),
                Paragraph(escape(item.description or "—"), normal),
                Paragraph(f"₹{money(item.amount):.2f}", normal),
                Paragraph(escape(item.payment_method.value.replace("_", " ").title()), normal),
            ]
        )
    report_table = Table(table_data, colWidths=[22 * mm, 20 * mm, 28 * mm, 62 * mm, 25 * mm, 25 * mm], repeatRows=1)
    report_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B241F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E6E0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F8F4")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(report_table)
    doc.build(story)
    return output.getvalue()
