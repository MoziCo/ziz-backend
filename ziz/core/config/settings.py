"""
Configuration settings for Ziz API.

Uses pydantic-settings for environment-based configuration.
"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # API Configuration
    api_title: str = "Ziz Evaluation API"
    api_description: str = (
        "User-experience-driven evaluation framework for AI applications"
    )
    api_version: str = "0.1.0"
    debug: bool = Field(default=False, description="Enable debug mode")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Host to bind the server")
    port: int = Field(default=8000, description="Port to bind the server")

    # Database Configuration
    mongodb_url: str = Field(
        default="mongodb://localhost:27017", description="MongoDB connection URL"
    )
    mongodb_db_name: str = Field(default="ziz_db", description="MongoDB database name")

    # Authentication Configuration
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens",
    )
    api_key_header: str = Field(
        default="X-API-Key", description="Header name for API key authentication"
    )

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["*"], description="List of allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(
        default=True, description="Allow credentials in CORS requests"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")

    # Pagination Limits
    default_page_size: int = Field(
        default=50, description="Default page size for pagination"
    )
    max_page_size: int = Field(
        default=1000, description="Maximum page size for pagination"
    )

    # Batch Processing Limits
    max_batch_size: int = Field(
        default=1000, description="Maximum batch size for bulk operations"
    )

    # Feature Flags
    enable_batch_endpoints: bool = Field(
        default=True, description="Enable batch processing endpoints"
    )

    @property
    def mongodb_connection_string(self) -> str:
        """Get the full MongoDB connection string."""
        return f"{self.mongodb_url}/{self.mongodb_db_name}"


# Global settings instance
settings = Settings()
