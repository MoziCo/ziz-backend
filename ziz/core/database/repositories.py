"""
Database repositories for data access.

Implements the repository pattern to abstract database operations.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from ziz.api.models.database import FeatureDocument, InteractionDocument, OutputDocument
from ziz.api.services.connection_manager import get_database

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common database operations."""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    async def _get_collection(self):
        """Get the collection from the database."""
        database = await get_database()
        return database[self.collection_name]

    async def create(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document."""
        document["created_at"] = datetime.now(UTC)
        document["updated_at"] = datetime.now(UTC)

        try:
            collection = await self._get_collection()
            result = await collection.insert_one(document)
            document["_id"] = result.inserted_id
            return document
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error in {self.collection_name}: {e}")
            raise ValueError("Document with this ID already exists")
        except Exception as e:
            logger.error(f"Error creating document in {self.collection_name}: {e}")
            raise

    async def get_by_id(self, id_field: str, id_value: str) -> Optional[Dict[str, Any]]:
        """Get a document by its ID field."""
        try:
            collection = await self._get_collection()
            return await collection.find_one({id_field: id_value})
        except Exception as e:
            logger.error(f"Error getting document from {self.collection_name}: {e}")
            raise

    async def update_by_id(
        self, id_field: str, id_value: str, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a document by its ID field."""
        update_data["updated_at"] = datetime.now(UTC)

        try:
            collection = await self._get_collection()
            result = await collection.find_one_and_update(
                {id_field: id_value}, {"$set": update_data}, return_document=True
            )
            return result
        except Exception as e:
            logger.error(f"Error updating document in {self.collection_name}: {e}")
            raise

    async def delete_by_id(self, id_field: str, id_value: str) -> bool:
        """Delete a document by its ID field."""
        try:
            collection = await self._get_collection()
            result = await collection.delete_one({id_field: id_value})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document from {self.collection_name}: {e}")
            raise

    async def list_with_pagination(
        self,
        filter_query: Dict[str, Any],
        limit: int,
        offset: int,
        sort_field: str = "created_at",
        sort_order: int = -1,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List documents with pagination."""
        try:
            collection = await self._get_collection()
            # Get total count
            total = await collection.count_documents(filter_query)

            # Get documents with pagination
            cursor = collection.find(filter_query)
            cursor = cursor.sort(sort_field, sort_order)
            cursor = cursor.skip(offset).limit(limit)

            documents = await cursor.to_list(length=limit)

            return documents, total
        except Exception as e:
            logger.error(f"Error listing documents from {self.collection_name}: {e}")
            raise


class FeatureRepository(BaseRepository):
    """Repository for feature operations."""

    def __init__(self):
        super().__init__("features")

    async def create_feature(self, feature_data: Dict[str, Any]) -> FeatureDocument:
        """Create a new feature."""
        if not feature_data.get("feature_id"):
            feature_data["feature_id"] = str(uuid4())

        document = await self.create(feature_data)
        return FeatureDocument(**document)

    async def get_feature(self, feature_id: str) -> Optional[FeatureDocument]:
        """Get a feature by ID."""
        document = await self.get_by_id("feature_id", feature_id)
        return FeatureDocument(**document) if document else None

    async def update_feature(
        self, feature_id: str, update_data: Dict[str, Any]
    ) -> Optional[FeatureDocument]:
        """Update a feature."""
        document = await self.update_by_id("feature_id", feature_id, update_data)
        return FeatureDocument(**document) if document else None

    async def list_features(
        self, limit: int, offset: int
    ) -> Tuple[List[FeatureDocument], int]:
        """List features with pagination."""
        documents, total = await self.list_with_pagination({}, limit, offset)
        features = [FeatureDocument(**doc) for doc in documents]
        return features, total


class OutputRepository(BaseRepository):
    """Repository for output operations."""

    def __init__(self):
        super().__init__("outputs")

    async def create_output(self, output_data: Dict[str, Any]) -> OutputDocument:
        """Create a new output."""
        if not output_data.get("output_id"):
            output_data["output_id"] = str(uuid4())

        if not output_data.get("timestamp"):
            output_data["timestamp"] = datetime.now(UTC)

        document = await self.create(output_data)
        return OutputDocument(**document)

    async def get_output(self, output_id: str) -> Optional[OutputDocument]:
        """Get an output by ID."""
        document = await self.get_by_id("output_id", output_id)
        return OutputDocument(**document) if document else None

    async def update_output(
        self, output_id: str, update_data: Dict[str, Any]
    ) -> Optional[OutputDocument]:
        """Update an output."""
        document = await self.update_by_id("output_id", output_id, update_data)
        return OutputDocument(**document) if document else None

    async def list_outputs_by_feature(
        self, feature_id: str, limit: int, offset: int
    ) -> Tuple[List[OutputDocument], int]:
        """List outputs for a specific feature."""
        filter_query = {"feature_id": feature_id}
        documents, total = await self.list_with_pagination(
            filter_query, limit, offset, sort_field="timestamp"
        )
        outputs = [OutputDocument(**doc) for doc in documents]
        return outputs, total

    async def feature_exists(self, feature_id: str) -> bool:
        """Check if a feature exists."""
        feature_repo = FeatureRepository()
        feature = await feature_repo.get_feature(feature_id)
        return feature is not None


class InteractionRepository(BaseRepository):
    """Repository for interaction operations."""

    def __init__(self):
        super().__init__("interactions")

    async def create_interaction(
        self, interaction_data: Dict[str, Any]
    ) -> InteractionDocument:
        """Create a new interaction."""
        if not interaction_data.get("interaction_id"):
            interaction_data["interaction_id"] = str(uuid4())

        if not interaction_data.get("timestamp"):
            interaction_data["timestamp"] = datetime.now(UTC)

        document = await self.create(interaction_data)
        return InteractionDocument(**document)

    async def get_interaction(
        self, interaction_id: str
    ) -> Optional[InteractionDocument]:
        """Get an interaction by ID."""
        document = await self.get_by_id("interaction_id", interaction_id)
        return InteractionDocument(**document) if document else None

    async def update_interaction(
        self, interaction_id: str, update_data: Dict[str, Any]
    ) -> Optional[InteractionDocument]:
        """Update an interaction."""
        document = await self.update_by_id(
            "interaction_id", interaction_id, update_data
        )
        return InteractionDocument(**document) if document else None

    async def list_interactions_by_output(
        self, output_id: str, limit: int, offset: int
    ) -> Tuple[List[InteractionDocument], int]:
        """List interactions for a specific output."""
        filter_query = {"output_id": output_id}
        documents, total = await self.list_with_pagination(
            filter_query, limit, offset, sort_field="timestamp"
        )
        interactions = [InteractionDocument(**doc) for doc in documents]
        return interactions, total

    async def output_exists(self, output_id: str) -> bool:
        """Check if an output exists."""
        output_repo = OutputRepository()
        output = await output_repo.get_output(output_id)
        return output is not None
