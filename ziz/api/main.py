"""
Ziz API Main Application

FastAPI application entry point for the Ziz evaluation system.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from ziz.api.middleware import APIKeyMiddleware
from ziz.api.routes import (
    feature_outputs_router,
    features_router,
    health_router,
    interactions_router,
    output_interactions_router,
    outputs_router,
)
from ziz.api.services.connection_manager import close_connections, get_database
from ziz.api.utils import (
    ZizAPIException,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    ziz_api_exception_handler,
)
from ziz.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_indexes():
    """Create database indexes for optimal performance."""
    try:
        database = await get_database()

        # Features collection indexes
        await database.features.create_index("feature_id", unique=True)
        await database.features.create_index("name")
        await database.features.create_index("created_at")

        # Outputs collection indexes
        await database.outputs.create_index("output_id", unique=True)
        await database.outputs.create_index("feature_id")
        await database.outputs.create_index("timestamp")
        await database.outputs.create_index("created_at")
        await database.outputs.create_index([("feature_id", 1), ("timestamp", -1)])

        # Interactions collection indexes
        await database.interactions.create_index("interaction_id", unique=True)
        await database.interactions.create_index("output_id")
        await database.interactions.create_index("type")
        await database.interactions.create_index("timestamp")
        await database.interactions.create_index("created_at")
        await database.interactions.create_index([("output_id", 1), ("timestamp", -1)])

        logger.info("Database indexes created successfully")

    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        # Don't raise here as indexes are optional for functionality


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    logger.info("Starting Ziz API...")
    try:
        # Test database connection and create indexes
        await get_database()
        await create_indexes()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Ziz API...")
    try:
        await close_connections()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API key authentication middleware
app.add_middleware(APIKeyMiddleware)

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ZizAPIException, ziz_api_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health_router)
app.include_router(features_router)
app.include_router(outputs_router)
app.include_router(interactions_router)
app.include_router(feature_outputs_router)
app.include_router(output_interactions_router)


def main():
    """Entry point for running the API server."""
    import uvicorn

    uvicorn.run(
        "ziz.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
