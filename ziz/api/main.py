"""
Ziz API Main Application

FastAPI application entry point for the Ziz evaluation system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Ziz Evaluation API",
    description="User-experience-driven evaluation framework for AI applications",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Ziz API is running", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {"status": "healthy", "service": "ziz-api"}


def main():
    """Entry point for running the API server."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
