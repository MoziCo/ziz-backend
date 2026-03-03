"""Abstract storage service interface and in-memory implementation.

The storage layer is decoupled via an abstract interface to allow future
swapping to MongoDB, a message broker, or any other persistence backend.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from ziz.api.models.feature import FeatureCreate, FeatureResponse
from ziz.api.models.interaction import InteractionCreate, InteractionResponse
from ziz.api.models.output import OutputCreate, OutputResponse


class StorageService(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def create_feature(self, data: FeatureCreate) -> FeatureResponse:
        """Create a feature. Raises ConflictError if feature_id already exists."""

    @abstractmethod
    async def get_feature(self, feature_id: str) -> FeatureResponse | None:
        """Get a feature by ID, or None if not found."""

    @abstractmethod
    async def create_output(self, data: OutputCreate) -> OutputResponse:
        """Create an output. Raises ConflictError if output_id already exists."""

    @abstractmethod
    async def get_output(self, output_id: str) -> OutputResponse | None:
        """Get an output by ID, or None if not found."""

    @abstractmethod
    async def list_outputs_by_feature(self, feature_id: str) -> list[OutputResponse]:
        """List all outputs for a given feature."""

    @abstractmethod
    async def create_interaction(self, data: InteractionCreate) -> InteractionResponse:
        """Create an interaction. Raises ConflictError if interaction_id already exists."""

    @abstractmethod
    async def get_interaction(self, interaction_id: str) -> InteractionResponse | None:
        """Get an interaction by ID, or None if not found."""

    @abstractmethod
    async def list_interactions_by_output(self, output_id: str) -> list[InteractionResponse]:
        """List all interactions for a given output."""


class ConflictError(Exception):
    """Raised when attempting to create a resource with a duplicate ID."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with id '{resource_id}' already exists")


class NotFoundError(Exception):
    """Raised when a referenced resource does not exist."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with id '{resource_id}' not found")


class InMemoryStorage(StorageService):
    """In-memory storage implementation for testing and development."""

    def __init__(self) -> None:
        self._features: dict[str, FeatureResponse] = {}
        self._outputs: dict[str, OutputResponse] = {}
        self._interactions: dict[str, InteractionResponse] = {}

    async def create_feature(self, data: FeatureCreate) -> FeatureResponse:
        if data.feature_id in self._features:
            raise ConflictError("Feature", data.feature_id)
        feature = FeatureResponse(
            feature_id=data.feature_id,
            name=data.name,
            metadata=data.metadata,
            created_at=datetime.now(timezone.utc),
        )
        self._features[data.feature_id] = feature
        return feature

    async def get_feature(self, feature_id: str) -> FeatureResponse | None:
        return self._features.get(feature_id)

    async def create_output(self, data: OutputCreate) -> OutputResponse:
        # Validate that the feature exists
        if data.feature_id not in self._features:
            raise NotFoundError("Feature", data.feature_id)
        if data.output_id in self._outputs:
            raise ConflictError("Output", data.output_id)
        output = OutputResponse(
            output_id=data.output_id,
            feature_id=data.feature_id,
            content=data.content,
            metadata=data.metadata,
            created_at=datetime.now(timezone.utc),
        )
        self._outputs[data.output_id] = output
        return output

    async def get_output(self, output_id: str) -> OutputResponse | None:
        return self._outputs.get(output_id)

    async def list_outputs_by_feature(self, feature_id: str) -> list[OutputResponse]:
        return [o for o in self._outputs.values() if o.feature_id == feature_id]

    async def create_interaction(self, data: InteractionCreate) -> InteractionResponse:
        # Validate that the output exists
        if data.output_id not in self._outputs:
            raise NotFoundError("Output", data.output_id)
        if data.interaction_id in self._interactions:
            raise ConflictError("Interaction", data.interaction_id)
        now = datetime.now(timezone.utc)
        interaction = InteractionResponse(
            interaction_id=data.interaction_id,
            output_id=data.output_id,
            interaction_type=data.interaction_type,
            metadata=data.metadata,
            timestamp=data.timestamp or now,
            created_at=now,
        )
        self._interactions[data.interaction_id] = interaction
        return interaction

    async def get_interaction(self, interaction_id: str) -> InteractionResponse | None:
        return self._interactions.get(interaction_id)

    async def list_interactions_by_output(self, output_id: str) -> list[InteractionResponse]:
        return [i for i in self._interactions.values() if i.output_id == output_id]
