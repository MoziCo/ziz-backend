"""
Storage service interface.

Provides an abstraction layer for data persistence that can be easily replaced
with message broker systems in the future.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from ziz.api.models.database import FeatureDocument, InteractionDocument, OutputDocument

logger = logging.getLogger(__name__)


class StorageService(ABC):
    """Abstract storage service interface."""

    @abstractmethod
    async def store_feature(self, feature_data: Dict[str, Any]) -> FeatureDocument:
        """Store a feature."""
        pass

    @abstractmethod
    async def get_feature(self, feature_id: str) -> Optional[FeatureDocument]:
        """Get a feature by ID."""
        pass

    @abstractmethod
    async def update_feature(
        self, feature_id: str, update_data: Dict[str, Any]
    ) -> Optional[FeatureDocument]:
        """Update a feature."""
        pass

    @abstractmethod
    async def list_features(
        self, limit: int, offset: int
    ) -> Tuple[List[FeatureDocument], int]:
        """List features with pagination."""
        pass

    @abstractmethod
    async def store_output(self, output_data: Dict[str, Any]) -> OutputDocument:
        """Store an output."""
        pass

    @abstractmethod
    async def get_output(self, output_id: str) -> Optional[OutputDocument]:
        """Get an output by ID."""
        pass

    @abstractmethod
    async def update_output(
        self, output_id: str, update_data: Dict[str, Any]
    ) -> Optional[OutputDocument]:
        """Update an output."""
        pass

    @abstractmethod
    async def list_outputs_by_feature(
        self, feature_id: str, limit: int, offset: int
    ) -> Tuple[List[OutputDocument], int]:
        """List outputs for a feature."""
        pass

    @abstractmethod
    async def store_interaction(
        self, interaction_data: Dict[str, Any]
    ) -> InteractionDocument:
        """Store an interaction."""
        pass

    @abstractmethod
    async def get_interaction(
        self, interaction_id: str
    ) -> Optional[InteractionDocument]:
        """Get an interaction by ID."""
        pass

    @abstractmethod
    async def update_interaction(
        self, interaction_id: str, update_data: Dict[str, Any]
    ) -> Optional[InteractionDocument]:
        """Update an interaction."""
        pass

    @abstractmethod
    async def list_interactions_by_output(
        self, output_id: str, limit: int, offset: int
    ) -> Tuple[List[InteractionDocument], int]:
        """List interactions for an output."""
        pass

    @abstractmethod
    async def feature_exists(self, feature_id: str) -> bool:
        """Check if a feature exists."""
        pass

    @abstractmethod
    async def output_exists(self, output_id: str) -> bool:
        """Check if an output exists."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the storage system."""
        pass
