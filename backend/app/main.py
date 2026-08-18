"""FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import error_response, unhandled_exception_handler
from app.database.session import SessionLocal
from app.services.recurring_service import process_due_transactions

settings = get_settings()
logger = logging.getLogger(__name__)


async def recurring_processor(stop_event: asyncio.Event) -> None:
    """Materialize due schedules on a timer even when no user opens the app."""
    interval_seconds = max(settings.recurring_processor_interval_minutes, 1) * 60
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
            continue
        except TimeoutError:
            pass
        try:
            with SessionLocal() as session:
                created = process_due_transactions(session)
                session.commit()
                if created:
                    logger.info("Materialized %s due recurring transaction(s)", created)
        except Exception:
            logger.exception("Recurring transaction processor failed; it will retry on the next interval")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting %s in %s mode", settings.app_name, settings.environment)
    stop_event = asyncio.Event()
    processor_task = asyncio.create_task(recurring_processor(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await processor_task
        logger.info("Stopping %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="REST API for the Spendly personal finance application.",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return error_response(exc.status_code, "request_error", str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
    return error_response(422, "validation_error", "Please correct the highlighted fields.", exc.errors())


app.add_exception_handler(Exception, unhandled_exception_handler)
app.include_router(api_router, prefix=settings.api_v1_prefix)
