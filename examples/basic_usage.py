"""
Basic usage examples for the Ziz SDK.

This example demonstrates the fundamental features of the Ziz SDK for logging
outputs and interactions from AI applications.
"""

import os
import time
from datetime import datetime

# Import the Ziz SDK
import ziz


# Example 1: Basic setup and usage
def basic_example():
    """Basic example showing simple output and interaction logging."""
    print("=== Basic Example ===")

    # Initialize the client
    client = ziz.Client(
        api_key="your-secret-key-change-in-production",  # In production, use env var
        feature_id="chatbot-v1",
        api_url="http://localhost:8000",  # Point to your local API
    )

    # Log an output
    output_id = client.log_output(
        content="Hello! I'm a helpful AI assistant. How can I help you today?",
        metadata={
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 150,
            "prompt": "You are a helpful assistant",
        },
    )

    print(f"Logged output with ID: {output_id}")

    # Log user feedback
    feedback_id = client.log_interaction(
        type="feedback",
        value="thumbs_up",
        output_id=output_id,
        metadata={"user_id": "user_123", "session_id": "session_456"},
    )

    print(f"Logged feedback with ID: {feedback_id}")

    # Use convenience methods
    thumbs_down_id = client.thumbs_down(
        output_id=output_id, metadata={"reason": "too_verbose"}
    )

    print(f"Logged thumbs down with ID: {thumbs_down_id}")

    # Manually flush any pending events
    client.flush()

    # Cleanup
    client.cleanup()


# Example 2: Using environment variables for configuration
def environment_config_example():
    """Example showing configuration via environment variables."""
    print("\n=== Environment Configuration Example ===")

    # Set environment variables (in practice, these would be set in your environment)
    os.environ["ZIZ_API_KEY"] = "your-secret-key-change-in-production"
    os.environ["ZIZ_API_URL"] = "http://localhost:8000"
    os.environ["ZIZ_FEATURE_ID"] = "recommendation-engine"
    os.environ["ZIZ_BATCH_SIZE"] = "10"
    os.environ["ZIZ_ALLOW_CONTENT"] = "true"  # Allow content logging

    # Client will automatically pick up environment variables
    client = ziz.Client()

    # Log a recommendation output
    output_id = client.log_output(
        content={
            "recommendations": [
                {"item": "Product A", "score": 0.95},
                {"item": "Product B", "score": 0.87},
                {"item": "Product C", "score": 0.72},
            ]
        },
        metadata={
            "user_id": "user_789",
            "algorithm": "collaborative_filtering",
            "num_recommendations": 3,
        },
    )

    print(f"Logged recommendation with ID: {output_id}")

    # Log user interaction (click)
    click_id = client.log_interaction(
        type="click",
        value="Product A",
        output_id=output_id,
        metadata={"click_position": 1, "timestamp": datetime.now().isoformat()},
    )

    print(f"Logged click interaction with ID: {click_id}")

    client.cleanup()


# Example 3: Microservice usage with separate services
def microservice_example():
    """Example showing usage across separate services."""
    print("\n=== Microservice Example ===")

    # Service A: Output Generator
    def service_a_generate_output():
        """Simulates Service A generating an output."""
        client = ziz.Client(
            api_key="your-secret-key-change-in-production",
            feature_id="text-generation",
            api_url="http://localhost:8000",
        )

        output_id = client.log_output(
            content="The quick brown fox jumps over the lazy dog.",
            metadata={
                "model": "text-davinci-003",
                "prompt": "Write a sentence with all letters of the alphabet",
                "service": "generator",
                "temperature": 0.3,
            },
        )

        print(f"Service A logged output: {output_id}")
        client.cleanup()
        return output_id

    # Service B: Interaction Logger
    def service_b_log_interaction(output_id):
        """Simulates Service B logging an interaction."""
        client = ziz.Client(
            api_key="your-secret-key-change-in-production",
            feature_id="text-generation",
            api_url="http://localhost:8000",
        )

        interaction_id = client.log_interaction(
            output_id=output_id,
            type="edit",
            value="The quick brown fox jumps over the lazy cat.",
            metadata={
                "editor": "user",
                "service": "editor",
                "edit_type": "word_replacement",
            },
        )

        print(f"Service B logged interaction: {interaction_id}")
        client.cleanup()
        return interaction_id

    # Simulate the workflow
    output_id = service_a_generate_output()
    service_b_log_interaction(output_id)


# Example 4: Advanced features - context manager
def context_manager_example():
    """Example showing context manager usage."""
    print("\n=== Context Manager Example ===")

    client = ziz.Client(
        api_key="your-secret-key-change-in-production",
        feature_id="code-generation",
        api_url="http://localhost:8000",
    )

    # Use context manager for automatic logging
    with client.track_output(metadata={"language": "python"}) as tracker:
        # Simulate code generation
        generated_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

        tracker.set_content(generated_code)
        tracker.add_metadata("lines_of_code", len(generated_code.split("\n")))

        # Add interactions
        tracker.feedback("positive")
        tracker.add_interaction(
            type="execution", value="success", metadata={"execution_time": 0.05}
        )

    print("Code generation tracked with context manager")
    client.cleanup()


# Example 5: Function decorator
def decorator_example():
    """Example showing function decorator usage."""
    print("\n=== Decorator Example ===")

    client = ziz.Client(
        api_key="your-secret-key-change-in-production",
        feature_id="language-translation",
        api_url="http://localhost:8000",
    )

    # Decorate a function to automatically track its outputs
    @ziz.track_output(
        client,
        content_extractor=lambda result: result["translated_text"],
        metadata_extractor=lambda args, result: {
            "source_language": args["source_lang"],
            "target_language": args["target_lang"],
            "confidence": result["confidence"],
        },
    )
    def translate_text(text, source_lang, target_lang):
        """Simulated translation function."""
        # This would normally call a real translation API
        return {
            "translated_text": f"[{target_lang.upper()}] {text}",
            "confidence": 0.95,
            "source_detected": source_lang,
        }

    # Use the decorated function
    result = translate_text("Hello world", "en", "es")
    print(f"Translation result: {result}")

    client.cleanup()


# Example 6: Error handling and privacy
def privacy_and_error_example():
    """Example showing privacy features and error handling."""
    print("\n=== Privacy and Error Handling Example ===")

    # Client with privacy-first settings (default)
    private_client = ziz.Client(
        api_key="your-secret-key-change-in-production",
        feature_id="sensitive-data-processing",
        api_url="http://localhost:8000",
        allow_content=False,  # Content will be redacted
        strict_mode=False,  # Don't raise exceptions on errors
    )

    # This content will be redacted due to privacy settings
    output_id = private_client.log_output(
        content="User email: john.doe@example.com, phone: 555-123-4567",
        metadata={"contains_pii": True},
    )

    print(f"Logged output with redaction: {output_id}")

    # Client that allows content (opt-in)
    open_client = ziz.Client(
        api_key="your-secret-key-change-in-production",
        feature_id="public-content",
        api_url="http://localhost:8000",
        allow_content=True,  # Content logging allowed
        strict_mode=True,  # Raise exceptions on errors
    )

    output_id = open_client.log_output(
        content="This is public content that can be logged", metadata={"public": True}
    )

    print(f"Logged public content: {output_id}")

    private_client.cleanup()
    open_client.cleanup()


# Example 7: Batch processing and performance
def batch_processing_example():
    """Example showing batch processing for high-throughput scenarios."""
    print("\n=== Batch Processing Example ===")

    client = ziz.Client(
        api_key="your-secret-key-change-in-production",
        feature_id="batch-processing",
        api_url="http://localhost:8000",
        batch_size=5,  # Small batch for demo
        batch_timeout=2.0,  # 2 second timeout
    )

    print("Logging multiple outputs (will be batched)...")

    # Log multiple outputs quickly
    output_ids = []
    for i in range(10):
        output_id = client.log_output(
            content=f"Batch output #{i}",
            metadata={"batch_index": i, "timestamp": time.time()},
        )
        output_ids.append(output_id)
        print(f"Queued output #{i}: {output_id}")

        # Small delay to see batching in action
        time.sleep(0.1)

    print(f"Pending events in batch: {client.get_pending_count()}")

    # Force flush remaining events
    client.flush()

    print("All events flushed")
    client.cleanup()


# Example 8: Custom interaction types
def custom_interactions_example():
    """Example showing custom interaction types."""
    print("\n=== Custom Interactions Example ===")

    client = ziz.Client(
        api_key="your-secret-key-change-in-production",
        feature_id="content-moderation",
        api_url="http://localhost:8000",
    )

    # Log content moderation output
    output_id = client.log_output(
        content="This is a sample user comment that needs moderation.",
        metadata={
            "moderation_score": 0.85,
            "categories": ["safe", "appropriate"],
            "flagged": False,
        },
    )

    # Log various custom interactions
    interactions = [
        ("human_review", "approved", {"reviewer": "moderator_1"}),
        ("automated_action", "published", {"action_time": time.time()}),
        ("user_report", "spam", {"reporter_id": "user_456"}),
        ("admin_override", "keep_published", {"admin_id": "admin_789"}),
    ]

    for interaction_type, value, metadata in interactions:
        interaction_id = client.log_interaction(
            type=interaction_type, value=value, output_id=output_id, metadata=metadata
        )
        print(f"Logged {interaction_type}: {interaction_id}")

    client.cleanup()


def main():
    """Run all examples."""
    print("Ziz SDK Examples")
    print("================")
    print("Make sure your Ziz API is running on http://localhost:8000")
    print()

    try:
        basic_example()
        environment_config_example()
        microservice_example()
        context_manager_example()
        decorator_example()
        privacy_and_error_example()
        batch_processing_example()
        custom_interactions_example()

        print("\n✅ All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("Make sure your Ziz API is running and accessible.")


if __name__ == "__main__":
    main()
