"""
Business logic services for Ziz API.

Contains the core business logic for features, outputs, and interactions.
"""

import logging
from typing import List, Optional, Tuple

from ziz.api.models import (
    BatchResponse,
    FeatureCreate,
    FeatureResponse,
    FeatureUpdate,
    InteractionBatchCreate,
    InteractionCreate,
    InteractionResponse,
    InteractionUpdate,
    OutputBatchCreate,
    OutputCreate,
    OutputResponse,
    OutputUpdate,
)
from ziz.api.services.mongodb_storage import storage_service
from ziz.api.services.storage import StorageService

logger = logging.getLogger(__name__)


class FeatureService:
    """Service for feature-related business logic."""

    def __init__(self, storage: StorageService = storage_service):
        self.storage = storage

    async def create_feature(self, feature_create: FeatureCreate) -> FeatureResponse:
        """Create a new feature."""
        feature_data = feature_create.model_dump(exclude_none=True)

        # Check if feature_id already exists (if provided)
        if feature_create.feature_id:
            existing = await self.storage.get_feature(feature_create.feature_id)
            if existing:
                raise ValueError(
                    f"Feature with ID '{feature_create.feature_id}' already exists"
                )

        feature_doc = await self.storage.store_feature(feature_data)
        return self._to_response(feature_doc)

    async def get_feature(self, feature_id: str) -> Optional[FeatureResponse]:
        """Get a feature by ID."""
        feature_doc = await self.storage.get_feature(feature_id)
        return self._to_response(feature_doc) if feature_doc else None

    async def update_feature(
        self, feature_id: str, feature_update: FeatureUpdate
    ) -> Optional[FeatureResponse]:
        """Update a feature."""
        update_data = feature_update.model_dump(exclude_none=True)
        if not update_data:
            # No fields to update
            return await self.get_feature(feature_id)

        feature_doc = await self.storage.update_feature(feature_id, update_data)
        return self._to_response(feature_doc) if feature_doc else None

    async def list_features(
        self, limit: int, offset: int
    ) -> Tuple[List[FeatureResponse], int]:
        """List features with pagination."""
        feature_docs, total = await self.storage.list_features(limit, offset)
        features = [self._to_response(doc) for doc in feature_docs]
        return features, total

    def _to_response(self, feature_doc) -> FeatureResponse:
        """Convert feature document to response model."""
        return FeatureResponse(
            feature_id=feature_doc.feature_id,
            name=feature_doc.name,
            metadata=feature_doc.metadata,
            created_at=feature_doc.created_at,
            updated_at=feature_doc.updated_at,
        )


class OutputService:
    """Service for output-related business logic."""

    def __init__(self, storage: StorageService = storage_service):
        self.storage = storage

    async def create_output(self, output_create: OutputCreate) -> OutputResponse:
        """Create a new output."""
        # Validate that feature exists
        if not await self.storage.feature_exists(output_create.feature_id):
            raise ValueError(f"Feature '{output_create.feature_id}' does not exist")

        # Check if output_id already exists (if provided)
        if output_create.output_id:
            existing = await self.storage.get_output(output_create.output_id)
            if existing:
                raise ValueError(
                    f"Output with ID '{output_create.output_id}' already exists"
                )

        output_data = output_create.model_dump(exclude_none=True)
        output_doc = await self.storage.store_output(output_data)
        return self._to_response(output_doc)

    async def get_output(self, output_id: str) -> Optional[OutputResponse]:
        """Get an output by ID."""
        output_doc = await self.storage.get_output(output_id)
        return self._to_response(output_doc) if output_doc else None

    async def update_output(
        self, output_id: str, output_update: OutputUpdate
    ) -> Optional[OutputResponse]:
        """Update an output."""
        update_data = output_update.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_output(output_id)

        output_doc = await self.storage.update_output(output_id, update_data)
        return self._to_response(output_doc) if output_doc else None

    async def list_outputs_by_feature(
        self, feature_id: str, limit: int, offset: int
    ) -> Tuple[List[OutputResponse], int]:
        """List outputs for a feature."""
        # Validate that feature exists
        if not await self.storage.feature_exists(feature_id):
            raise ValueError(f"Feature '{feature_id}' does not exist")

        output_docs, total = await self.storage.list_outputs_by_feature(
            feature_id, limit, offset
        )
        outputs = [self._to_response(doc) for doc in output_docs]
        return outputs, total

    async def create_outputs_batch(
        self, batch_create: OutputBatchCreate
    ) -> BatchResponse:
        """Create multiple outputs in batch."""
        success_count = 0
        failure_count = 0
        errors = []

        for i, output_create in enumerate(batch_create.outputs):
            try:
                await self.create_output(output_create)
                success_count += 1
            except Exception as e:
                failure_count += 1
                errors.append({
                    "index": i,
                    "output_id": output_create.output_id,
                    "error": str(e),
                })
                logger.error(f"Failed to create output at index {i}: {e}")

        return BatchResponse(
            success_count=success_count, failure_count=failure_count, errors=errors
        )

    def _to_response(self, output_doc) -> OutputResponse:
        """Convert output document to response model."""
        return OutputResponse(
            output_id=output_doc.output_id,
            feature_id=output_doc.feature_id,
            content=output_doc.content,
            metadata=output_doc.metadata,
            timestamp=output_doc.timestamp,
            created_at=output_doc.created_at,
            updated_at=output_doc.updated_at,
        )


class InteractionService:
    """Service for interaction-related business logic."""

    def __init__(self, storage: StorageService = storage_service):
        self.storage = storage

    async def create_interaction(
        self, interaction_create: InteractionCreate
    ) -> InteractionResponse:
        """Create a new interaction."""
        # Validate that output exists
        if not await self.storage.output_exists(interaction_create.output_id):
            raise ValueError(f"Output '{interaction_create.output_id}' does not exist")

        # Check if interaction_id already exists (if provided)
        if interaction_create.interaction_id:
            existing = await self.storage.get_interaction(
                interaction_create.interaction_id
            )
            if existing:
                raise ValueError(
                    f"Interaction with ID '{interaction_create.interaction_id}' already exists"
                )

        interaction_data = interaction_create.model_dump(exclude_none=True)
        interaction_doc = await self.storage.store_interaction(interaction_data)
        return self._to_response(interaction_doc)

    async def get_interaction(
        self, interaction_id: str
    ) -> Optional[InteractionResponse]:
        """Get an interaction by ID."""
        interaction_doc = await self.storage.get_interaction(interaction_id)
        return self._to_response(interaction_doc) if interaction_doc else None

    async def update_interaction(
        self, interaction_id: str, interaction_update: InteractionUpdate
    ) -> Optional[InteractionResponse]:
        """Update an interaction."""
        update_data = interaction_update.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_interaction(interaction_id)

        interaction_doc = await self.storage.update_interaction(
            interaction_id, update_data
        )
        return self._to_response(interaction_doc) if interaction_doc else None

    async def list_interactions_by_output(
        self, output_id: str, limit: int, offset: int
    ) -> Tuple[List[InteractionResponse], int]:
        """List interactions for an output."""
        # Validate that output exists
        if not await self.storage.output_exists(output_id):
            raise ValueError(f"Output '{output_id}' does not exist")

        interaction_docs, total = await self.storage.list_interactions_by_output(
            output_id, limit, offset
        )
        interactions = [self._to_response(doc) for doc in interaction_docs]
        return interactions, total

    async def create_interactions_batch(
        self, batch_create: InteractionBatchCreate
    ) -> BatchResponse:
        """Create multiple interactions in batch."""
        success_count = 0
        failure_count = 0
        errors = []

        for i, interaction_create in enumerate(batch_create.interactions):
            try:
                await self.create_interaction(interaction_create)
                success_count += 1
            except Exception as e:
                failure_count += 1
                errors.append({
                    "index": i,
                    "interaction_id": interaction_create.interaction_id,
                    "error": str(e),
                })
                logger.error(f"Failed to create interaction at index {i}: {e}")

        return BatchResponse(
            success_count=success_count, failure_count=failure_count, errors=errors
        )

    def _to_response(self, interaction_doc) -> InteractionResponse:
        """Convert interaction document to response model."""
        return InteractionResponse(
            interaction_id=interaction_doc.interaction_id,
            output_id=interaction_doc.output_id,
            type=interaction_doc.type,
            value=interaction_doc.value,
            metadata=interaction_doc.metadata,
            timestamp=interaction_doc.timestamp,
            created_at=interaction_doc.created_at,
            updated_at=interaction_doc.updated_at,
        )
