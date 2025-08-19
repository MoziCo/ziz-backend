"""
Tests for Pydantic models.

Tests validation and serialization of API models.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ziz.api.models import (
    FeatureCreate,
    FeatureResponse,
    InteractionBatchCreate,
    InteractionCreate,
    InteractionResponse,
    OutputBatchCreate,
    OutputCreate,
    OutputResponse,
)


def test_feature_create_model():
    """Test FeatureCreate model validation."""
    # Valid feature
    feature = FeatureCreate(name="Test Feature", metadata={"key": "value"})
    assert feature.name == "Test Feature"
    assert feature.metadata == {"key": "value"}
    assert feature.feature_id is None

    # Feature with custom ID
    feature_with_id = FeatureCreate(feature_id="custom-id", name="Test Feature")
    assert feature_with_id.feature_id == "custom-id"

    # Invalid feature (missing name)
    with pytest.raises(ValidationError):
        FeatureCreate()


def test_output_create_model():
    """Test OutputCreate model validation."""
    # Valid output
    output = OutputCreate(
        feature_id="feature-123",
        content="This is test content",
        metadata={"model": "gpt-4"},
    )
    assert output.feature_id == "feature-123"
    assert output.content == "This is test content"
    assert output.metadata == {"model": "gpt-4"}

    # Output with complex content
    complex_output = OutputCreate(
        feature_id="feature-123",
        content={
            "text": "Generated text",
            "confidence": 0.95,
            "tokens": ["generated", "text"],
        },
    )
    assert isinstance(complex_output.content, dict)

    # Invalid output (missing feature_id)
    with pytest.raises(ValidationError):
        OutputCreate(content="test")


def test_interaction_create_model():
    """Test InteractionCreate model validation."""
    # Valid interaction
    interaction = InteractionCreate(
        output_id="output-123",
        type="feedback",
        value="thumbs_up",
        metadata={"user_id": "user-1"},
    )
    assert interaction.output_id == "output-123"
    assert interaction.type == "feedback"
    assert interaction.value == "thumbs_up"

    # Interaction with complex value
    complex_interaction = InteractionCreate(
        output_id="output-123",
        type="edit",
        value={
            "original": "Hello world",
            "edited": "Hello there",
            "changes": [{"pos": 6, "old": "world", "new": "there"}],
        },
    )
    assert isinstance(complex_interaction.value, dict)

    # Invalid interaction (missing required fields)
    with pytest.raises(ValidationError):
        InteractionCreate(type="feedback")


def test_batch_models():
    """Test batch creation models."""
    # Valid output batch
    output_batch = OutputBatchCreate(
        outputs=[
            OutputCreate(feature_id="f1", content="content1"),
            OutputCreate(feature_id="f2", content="content2"),
        ]
    )
    assert len(output_batch.outputs) == 2

    # Valid interaction batch
    interaction_batch = InteractionBatchCreate(
        interactions=[
            InteractionCreate(output_id="o1", type="feedback", value="up"),
            InteractionCreate(output_id="o2", type="feedback", value="down"),
        ]
    )
    assert len(interaction_batch.interactions) == 2

    # Invalid batch (empty)
    with pytest.raises(ValidationError):
        OutputBatchCreate(outputs=[])


def test_response_models():
    """Test response model creation."""
    # Feature response
    feature_response = FeatureResponse(
        feature_id="f1",
        name="Test Feature",
        metadata={"key": "value"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert feature_response.feature_id == "f1"
    assert feature_response.name == "Test Feature"

    # Output response
    output_response = OutputResponse(
        output_id="o1",
        feature_id="f1",
        content="test content",
        metadata={},
        timestamp=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert output_response.output_id == "o1"
    assert output_response.feature_id == "f1"

    # Interaction response
    interaction_response = InteractionResponse(
        interaction_id="i1",
        output_id="o1",
        type="feedback",
        value="thumbs_up",
        metadata={},
        timestamp=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert interaction_response.interaction_id == "i1"
    assert interaction_response.output_id == "o1"
