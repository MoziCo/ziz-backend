"""API Routes module."""

from .features import router as features_router
from .health import router as health_router
from .interactions import output_interactions_router
from .interactions import router as interactions_router
from .outputs import feature_outputs_router
from .outputs import router as outputs_router

__all__ = [
    "features_router",
    "outputs_router",
    "interactions_router",
    "health_router",
    "feature_outputs_router",
    "output_interactions_router",
]
