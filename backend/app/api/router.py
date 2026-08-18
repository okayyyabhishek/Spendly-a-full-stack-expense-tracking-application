"""Top-level API router. Feature routers are added as modules are implemented."""

from fastapi import APIRouter

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.budgets import router as budgets_router
from app.api.categories import router as categories_router
from app.api.export import router as export_router
from app.api.health import router as health_router
from app.api.recurring import router as recurring_router
from app.api.notifications import router as notifications_router
from app.api.transactions import router as transactions_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(transactions_router)
api_router.include_router(budgets_router)
api_router.include_router(recurring_router)
api_router.include_router(analytics_router)
api_router.include_router(notifications_router)
api_router.include_router(export_router)
