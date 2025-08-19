"""
MongoDB implementation of the storage service.

This implementation uses MongoDB repositories for data persistence.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from ziz.api.models.database import FeatureDocument, InteractionDocument, OutputDocument
from ziz.api.services.connection_manager import get_database
from ziz.api.services.storage import StorageService
from ziz.core.database import FeatureRepository, InteractionRepository, OutputRepository

logger = logging.getLogger(__name__)


class MongoDBStorageService(StorageService):
    """MongoDB implementation of the storage service."""

    def __init__(self):
        self._feature_repo: Optional[FeatureRepository] = None
        self._output_repo: Optional[OutputRepository] = None
        self._interaction_repo: Optional[InteractionRepository] = None

    @property
    def feature_repo(self) -> FeatureRepository:
        """Get feature repository instance."""
        if self._feature_repo is None:
            self._feature_repo = FeatureRepository()
        return self._feature_repo

    @property
    def output_repo(self) -> OutputRepository:
        """Get output repository instance."""
        if self._output_repo is None:
            self._output_repo = OutputRepository()
        return self._output_repo

    @property
    def interaction_repo(self) -> InteractionRepository:
        """Get interaction repository instance."""
        if self._interaction_repo is None:
            self._interaction_repo = InteractionRepository()
        return self._interaction_repo

    async def store_feature(self, feature_data: Dict[str, Any]) -> FeatureDocument:
        """Store a feature in MongoDB."""
        logger.info(
            f"Storing feature: {feature_data.get('feature_id', 'auto-generated')}"
        )
        return await self.feature_repo.create_feature(feature_data)

    async def get_feature(self, feature_id: str) -> Optional[FeatureDocument]:
        """Get a feature from MongoDB."""
        return await self.feature_repo.get_feature(feature_id)

    async def update_feature(
        self, feature_id: str, update_data: Dict[str, Any]
    ) -> Optional[FeatureDocument]:
        """Update a feature in MongoDB."""
        logger.info(f"Updating feature: {feature_id}")
        return await self.feature_repo.update_feature(feature_id, update_data)

    async def list_features(
        self, limit: int, offset: int
    ) -> Tuple[List[FeatureDocument], int]:
        """List features from MongoDB."""
        return await self.feature_repo.list_features(limit, offset)

    async def store_output(self, output_data: Dict[str, Any]) -> OutputDocument:
        """Store an output in MongoDB."""
        logger.info(
            f"Storing output: {output_data.get('output_id', 'auto-generated')} for feature: {output_data.get('feature_id')}"
        )
        return await self.output_repo.create_output(output_data)

    async def get_output(self, output_id: str) -> Optional[OutputDocument]:
        """Get an output from MongoDB."""
        return await self.output_repo.get_output(output_id)

    async def update_output(
        self, output_id: str, update_data: Dict[str, Any]
    ) -> Optional[OutputDocument]:
        """Update an output in MongoDB."""
        logger.info(f"Updating output: {output_id}")
        return await self.output_repo.update_output(output_id, update_data)

    async def list_outputs_by_feature(
        self, feature_id: str, limit: int, offset: int
    ) -> Tuple[List[OutputDocument], int]:
        """List outputs for a feature from MongoDB."""
        return await self.output_repo.list_outputs_by_feature(feature_id, limit, offset)

    async def store_interaction(
        self, interaction_data: Dict[str, Any]
    ) -> InteractionDocument:
        """Store an interaction in MongoDB."""
        logger.info(
            f"Storing interaction: {interaction_data.get('interaction_id', 'auto-generated')} for output: {interaction_data.get('output_id')}"
        )
        return await self.interaction_repo.create_interaction(interaction_data)

    async def get_interaction(
        self, interaction_id: str
    ) -> Optional[InteractionDocument]:
        """Get an interaction from MongoDB."""
        return await self.interaction_repo.get_interaction(interaction_id)

    async def update_interaction(
        self, interaction_id: str, update_data: Dict[str, Any]
    ) -> Optional[InteractionDocument]:
        """Update an interaction in MongoDB."""
        logger.info(f"Updating interaction: {interaction_id}")
        return await self.interaction_repo.update_interaction(
            interaction_id, update_data
        )

    async def list_interactions_by_output(
        self, output_id: str, limit: int, offset: int
    ) -> Tuple[List[InteractionDocument], int]:
        """List interactions for an output from MongoDB."""
        return await self.interaction_repo.list_interactions_by_output(
            output_id, limit, offset
        )

    async def feature_exists(self, feature_id: str) -> bool:
        """Check if a feature exists in MongoDB."""
        return await self.output_repo.feature_exists(feature_id)

    async def output_exists(self, output_id: str) -> bool:
        """Check if an output exists in MongoDB."""
        return await self.interaction_repo.output_exists(output_id)

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on MongoDB."""
        try:
            database = await get_database()
            # Simple ping to check connection
            await database.command("ping")

            # Get database stats
            stats = await database.command("dbStats")

            return {
                "status": "healthy",
                "database": database.name,
                "collections": stats.get("collections", 0),
                "dataSize": stats.get("dataSize", 0),
                "indexSize": stats.get("indexSize", 0),
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}


# Global storage service instance
storage_service = MongoDBStorageService()
