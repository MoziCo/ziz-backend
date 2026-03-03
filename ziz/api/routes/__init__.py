"""Ziz API route modules."""

from ziz.api.routes.features import router as features_router
from ziz.api.routes.interactions import router as interactions_router
from ziz.api.routes.outputs import router as outputs_router
from ziz.api.routes.query import router as query_router

__all__ = [
    "features_router",
    "interactions_router",
    "outputs_router",
    "query_router",
]
