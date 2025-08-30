"""
Comprehensive tests for the Ziz SDK.

Tests all major SDK functionality including clients, batching, retries, etc.
"""

import os
import time
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ziz.sdk import (
    AsyncClient,
    Client,
    Interaction,
    Output,
    OutputTracker,
    RedactionManager,
    RetryManager,
    ZizConfig,
)
from ziz.sdk.client.batch import BatchManager
from ziz.sdk.decorators import track_function, track_output


class TestZizConfig:
    """Test ZizConfig functionality."""

    def test_config_from_env(self):
        """Test configuration creation from environment variables."""
        with patch.dict(
            os.environ,
            {
                "ZIZ_API_KEY": "test-key",
                "ZIZ_API_URL": "https://test.api.com",
                "ZIZ_FEATURE_ID": "test-feature",
                "ZIZ_BATCH_SIZE": "50",
                "ZIZ_ALLOW_CONTENT": "true",
            },
        ):
            config = ZizConfig.from_env()

            assert config.api_key == "test-key"
            assert config.api_url == "https://test.api.com"
            assert config.feature_id == "test-feature"
            assert config.batch_size == 50
            assert config.allow_content is True

    def test_config_overrides(self):
        """Test configuration overrides."""
        config = ZizConfig.from_env(
            api_key="override-key", batch_size=200, strict_mode=True
        )

        assert config.api_key == "override-key"
        assert config.batch_size == 200
        assert config.strict_mode is True


class TestRedactionManager:
    """Test RedactionManager functionality."""

    def test_email_redaction(self):
        """Test email address redaction."""
        redactor = RedactionManager()
        text = "Contact us at support@example.com for help"
        result = redactor.redact_text(text)
        assert "[EMAIL]" in result
        assert "support@example.com" not in result

    def test_phone_redaction(self):
        """Test phone number redaction."""
        redactor = RedactionManager()
        text = "Call us at 555-123-4567"
        result = redactor.redact_text(text)
        assert "[PHONE]" in result
        assert "555-123-4567" not in result

    def test_custom_rule(self):
        """Test custom redaction rules."""
        from ziz.sdk.utils.redaction import RedactionRule

        redactor = RedactionManager()
        custom_rule = RedactionRule(r"\bpassword:\s*\w+", "[PASSWORD]", "Passwords")
        redactor.add_rule(custom_rule)

        text = "Login with password: secret123"
        result = redactor.redact_text(text)
        assert "[PASSWORD]" in result
        assert "secret123" not in result

    def test_dict_redaction(self):
        """Test dictionary redaction."""
        redactor = RedactionManager()
        data = {
            "user": "john@example.com",
            "password": "secret",
            "message": "Hello world",
        }

        result = redactor.redact_dict(data)
        assert "[EMAIL]" in result["user"]
        assert result["password"] == "[REDACTED]"  # Sensitive key
        assert result["message"] == "Hello world"  # Not sensitive

    def test_disabled_redaction(self):
        """Test disabled redaction."""
        redactor = RedactionManager(enabled=False)
        text = "Email: test@example.com"
        result = redactor.redact_text(text)
        assert result == text  # Should be unchanged


class TestRetryManager:
    """Test RetryManager functionality."""

    def test_successful_retry(self):
        """Test successful operation after retries."""
        retry_manager = RetryManager(max_attempts=3)

        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"

        result = retry_manager.retry_sync(failing_func)
        assert result == "success"
        assert call_count == 3

    def test_max_attempts_exceeded(self):
        """Test max attempts exceeded."""
        retry_manager = RetryManager(max_attempts=2)

        def always_failing_func():
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            retry_manager.retry_sync(always_failing_func)

    def test_non_retryable_error(self):
        """Test non-retryable errors."""
        retry_manager = RetryManager(max_attempts=3)

        call_count = 0

        def func_with_non_retryable_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Bad input")  # Not retryable

        with pytest.raises(ValueError):
            retry_manager.retry_sync(func_with_non_retryable_error)

        assert call_count == 1  # Should not retry

    @pytest.mark.asyncio
    async def test_async_retry(self):
        """Test async retry functionality."""
        retry_manager = RetryManager(max_attempts=3, base_delay=0.01)

        call_count = 0

        async def failing_async_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "async_success"

        result = await retry_manager.retry_async(failing_async_func)
        assert result == "async_success"
        assert call_count == 3


class TestBatchManager:
    """Test BatchManager functionality."""

    def test_batch_size_flush(self):
        """Test flushing when batch size is reached."""
        flush_calls = []

        def mock_flush(batch):
            flush_calls.append(batch)

        batch_manager = BatchManager(
            flush_func=mock_flush,
            batch_size=2,
            auto_flush=False,  # Disable time-based flushing
        )

        # Create test outputs
        output1 = Output(feature_id="test", content="content1")
        output2 = Output(feature_id="test", content="content2")
        output3 = Output(feature_id="test", content="content3")

        # Add outputs
        batch_manager.add_output(output1)
        assert len(flush_calls) == 0  # Not yet at batch size

        batch_manager.add_output(output2)
        time.sleep(0.1)  # Allow background flush to complete
        assert len(flush_calls) == 1  # Should have flushed

        batch_manager.add_output(output3)
        assert len(flush_calls) == 1  # Still only one flush

        batch_manager.shutdown()

    def test_manual_flush(self):
        """Test manual flush functionality."""
        flush_calls = []

        def mock_flush(batch):
            flush_calls.append(batch)

        batch_manager = BatchManager(
            flush_func=mock_flush,
            batch_size=10,  # Large batch size
            auto_flush=False,
        )

        output = Output(feature_id="test", content="content")
        batch_manager.add_output(output)

        assert len(flush_calls) == 0

        batch_manager.flush()
        time.sleep(0.1)  # Allow background flush to complete
        assert len(flush_calls) == 1

        batch_manager.shutdown()


class TestZizClient:
    """Test sync ZizClient functionality."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        with patch("ziz.sdk.client.sync.requests.Session") as mock_session:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_response.content = b'{"success": true}'

            mock_session.return_value.request.return_value = mock_response

            client = Client(
                api_key="test-key",
                feature_id="test-feature",
                batch_size=2,  # Small batch for testing
                batch_timeout=0.1,
            )
            yield client
            client.cleanup()

    def test_client_initialization(self):
        """Test client initialization."""
        client = Client(api_key="test-key", feature_id="test-feature")

        assert client.config.api_key == "test-key"
        assert client.config.feature_id == "test-feature"
        client.cleanup()

    def test_client_initialization_no_api_key(self):
        """Test client initialization without API key."""
        with pytest.raises(ValueError, match="API key is required"):
            Client()

    def test_log_output(self, mock_client):
        """Test logging an output."""
        output_id = mock_client.log_output("Test content", metadata={"model": "test"})

        assert output_id is not None
        assert mock_client.last_output_id == output_id

    def test_log_interaction(self, mock_client):
        """Test logging an interaction."""
        # First log an output
        mock_client.log_output("Test content")

        # Then log an interaction
        interaction_id = mock_client.log_interaction("feedback", "thumbs_up")

        assert interaction_id is not None

    def test_convenience_methods(self, mock_client):
        """Test convenience methods."""
        mock_client.log_output("Test content")

        feedback_id = mock_client.feedback("positive")
        thumbs_up_id = mock_client.thumbs_up()
        thumbs_down_id = mock_client.thumbs_down()

        assert all(id is not None for id in [feedback_id, thumbs_up_id, thumbs_down_id])

    def test_sync_logging(self, mock_client):
        """Test synchronous logging (bypassing batch)."""
        with patch.object(mock_client, "_make_request") as mock_request:
            mock_request.return_value.success = True
            mock_request.return_value.data = {"output_id": "test-id"}

            output_id = mock_client.log_output_sync("Test content")
            assert output_id is not None
            mock_request.assert_called_once()


class TestAsyncZizClient:
    """Test async ZizClient functionality."""

    @pytest.fixture
    async def mock_async_client(self):
        """Create a mock async client for testing."""
        with patch("ziz.sdk.client.async_client.aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value='{"success": true}')
            mock_response.request_info = Mock()
            mock_response.history = []

            mock_session.return_value.__aenter__.return_value = mock_response
            mock_session.return_value.request.return_value.__aenter__.return_value = (
                mock_response
            )

            client = AsyncClient(
                api_key="test-key",
                feature_id="test-feature",
                batch_size=2,
                batch_timeout=0.1,
            )
            yield client
            await client.aclose()

    @pytest.mark.asyncio
    async def test_async_log_output(self, mock_async_client):
        """Test async output logging."""
        output_id = await mock_async_client.log_output("Test content async")

        assert output_id is not None
        assert mock_async_client.last_output_id == output_id

    @pytest.mark.asyncio
    async def test_async_log_interaction(self, mock_async_client):
        """Test async interaction logging."""
        await mock_async_client.log_output("Test content")
        interaction_id = await mock_async_client.log_interaction(
            "feedback", "thumbs_up"
        )

        assert interaction_id is not None

    @pytest.mark.asyncio
    async def test_async_convenience_methods(self, mock_async_client):
        """Test async convenience methods."""
        await mock_async_client.log_output("Test content")

        feedback_id = await mock_async_client.feedback("positive")
        thumbs_up_id = await mock_async_client.thumbs_up()

        assert all(id is not None for id in [feedback_id, thumbs_up_id])

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_async_client):
        """Test async context manager."""
        async with mock_async_client as client:
            output_id = await client.log_output("Context manager test")
            assert output_id is not None


class TestOutputTracker:
    """Test OutputTracker context manager."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        client = Mock()
        client.log_output.return_value = "output-123"
        client.log_interaction.return_value = "interaction-456"
        return client

    def test_output_tracker_basic(self, mock_client):
        """Test basic OutputTracker functionality."""
        with OutputTracker(mock_client, feature_id="test-feature") as tracker:
            tracker.set_content("Test output content")
            tracker.add_interaction("feedback", "thumbs_up")

        # Check that output and interaction were logged
        mock_client.log_output.assert_called_once()
        mock_client.log_interaction.assert_called_once()

    def test_output_tracker_convenience_methods(self, mock_client):
        """Test OutputTracker convenience methods."""
        with OutputTracker(mock_client, feature_id="test-feature") as tracker:
            tracker.set_content("Test content")
            tracker.thumbs_up()
            tracker.thumbs_down()
            tracker.feedback("custom feedback")
            tracker.edit("edited content")

        # Should have called log_interaction multiple times
        assert mock_client.log_interaction.call_count == 4

    def test_output_tracker_metadata(self, mock_client):
        """Test OutputTracker metadata handling."""
        with OutputTracker(
            mock_client, feature_id="test-feature", metadata={"initial": "data"}
        ) as tracker:
            tracker.set_content("Test content")
            tracker.add_metadata("additional", "metadata")
            tracker.update_metadata({"more": "data"})

        # Check that metadata was passed correctly
        call_args = mock_client.log_output.call_args
        metadata = call_args[1]["metadata"]
        assert metadata["initial"] == "data"
        assert metadata["additional"] == "metadata"
        assert metadata["more"] == "data"


class TestDecorators:
    """Test decorator functionality."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        client = Mock()
        client.log_output.return_value = "output-123"
        return client

    def test_track_output_decorator(self, mock_client):
        """Test track_output decorator."""

        @track_output(mock_client, feature_id="test-feature")
        def test_function(x, y):
            return x + y

        result = test_function(2, 3)

        assert result == 5
        mock_client.log_output.assert_called_once()

        # Check that the result was logged as content
        call_args = mock_client.log_output.call_args
        assert call_args[1]["content"] == 5

    def test_track_output_with_extractor(self, mock_client):
        """Test track_output decorator with content extractor."""

        @track_output(
            mock_client,
            feature_id="test-feature",
            content_extractor=lambda result: result["text"],
            metadata_extractor=lambda args, result: {"tokens": result["tokens"]},
        )
        def test_function():
            return {"text": "Generated text", "tokens": 10}

        test_function()

        mock_client.log_output.assert_called_once()
        call_args = mock_client.log_output.call_args
        assert call_args[1]["content"] == "Generated text"
        assert call_args[1]["metadata"]["tokens"] == 10

    def test_track_function_decorator(self, mock_client):
        """Test track_function decorator."""

        @track_function(mock_client, feature_id="test-feature")
        def test_function(value):
            if value == "error":
                raise ValueError("Test error")
            return f"processed: {value}"

        # Test successful call
        result = test_function("hello")
        assert result == "processed: hello"

        # Should have logged call and result
        assert mock_client.log_output.call_count == 2

        # Test error case
        mock_client.reset_mock()
        with pytest.raises(ValueError):
            test_function("error")

        # Should have logged call and error
        assert mock_client.log_output.call_count == 2


class TestModels:
    """Test Pydantic models."""

    def test_output_creation(self):
        """Test Output model creation."""
        output = Output(
            feature_id="test-feature",
            content="Test content",
            metadata={"model": "test"},
        )

        assert output.feature_id == "test-feature"
        assert output.content == "Test content"
        assert output.output_id is not None  # Auto-generated
        assert output.timestamp is not None  # Auto-generated
        assert isinstance(output.timestamp, datetime)

    def test_interaction_creation(self):
        """Test Interaction model creation."""
        interaction = Interaction(
            output_id="output-123", type="feedback", value="thumbs_up"
        )

        assert interaction.output_id == "output-123"
        assert interaction.type == "feedback"
        assert interaction.value == "thumbs_up"
        assert interaction.interaction_id is not None  # Auto-generated
        assert interaction.timestamp is not None  # Auto-generated

    def test_ziz_config_validation(self):
        """Test ZizConfig validation."""
        config = ZizConfig(api_key="test-key")

        assert config.api_key == "test-key"
        assert config.api_url == "https://api.ziz.ai"  # Default value
        assert config.batch_size == 100  # Default value
        assert config.allow_content is False  # Privacy default


class TestIntegration:
    """Integration tests combining multiple components."""

    @pytest.mark.asyncio
    async def test_full_workflow_async(self):
        """Test complete async workflow."""
        with patch("ziz.sdk.client.async_client.aiohttp.ClientSession") as mock_session:
            # Mock successful responses
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value='{"success": true}')
            mock_response.request_info = Mock()
            mock_response.history = []

            mock_session.return_value.request.return_value.__aenter__.return_value = (
                mock_response
            )

            # Create client
            async with AsyncClient(
                api_key="test-key",
                feature_id="integration-test",
                batch_size=1,  # Immediate flush
                batch_timeout=0.1,
            ) as client:
                # Log output
                output_id = await client.log_output(
                    "Integration test output", metadata={"test": "integration"}
                )

                # Log interaction
                interaction_id = await client.log_interaction(
                    "feedback", "positive", output_id=output_id
                )

                # Use convenience method
                thumbs_up_id = await client.thumbs_up(output_id)

                assert all(
                    id is not None for id in [output_id, interaction_id, thumbs_up_id]
                )

    def test_error_handling_strict_mode(self):
        """Test error handling in strict mode."""
        client = Client(
            api_key="test-key", feature_id="test", strict_mode=True, batch_size=1
        )

        # Mock a failing request
        with patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = Exception("Network error")

            # Should raise exception in strict mode
            with pytest.raises(Exception):  # noqa: B017
                client.log_output_sync("Test content")

        client.cleanup()

    def test_error_handling_non_strict_mode(self):
        """Test error handling in non-strict mode."""
        client = Client(
            api_key="test-key", feature_id="test", strict_mode=False, batch_size=1
        )

        # Mock a failing request
        with patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = Exception("Network error")

            # Should not raise exception in non-strict mode
            result = client.log_output_sync("Test content")
            assert result is None  # Should return None on error

        client.cleanup()


if __name__ == "__main__":
    pytest.main([__file__])
