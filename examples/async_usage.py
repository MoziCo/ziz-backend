"""
Async usage examples for the Ziz SDK.

This example demonstrates how to use the async features of the Ziz SDK
for high-performance applications and async frameworks.
"""

import asyncio
import time

# Import the Ziz SDK
import ziz


async def basic_async_example():
    """Basic async example showing async output and interaction logging."""
    print("=== Basic Async Example ===")

    # Initialize async client
    async with ziz.AsyncClient(
        api_key="your-secret-key-change-in-production",
        feature_id="async-chatbot",
        api_url="http://localhost:8000",
    ) as client:
        # Log an output asynchronously
        output_id = await client.log_output(
            content="Hello! I'm an async AI assistant.",
            metadata={"model": "async-gpt-4", "response_time": 0.25, "async": True},
        )

        print(f"Async logged output: {output_id}")

        # Log interaction asynchronously
        feedback_id = await client.log_interaction(
            type="feedback",
            value="thumbs_up",
            output_id=output_id,
            metadata={"async_feedback": True},
        )

        print(f"Async logged feedback: {feedback_id}")

        # Use async convenience methods
        thumbs_up_id = await client.thumbs_up(output_id)
        print(f"Async thumbs up: {thumbs_up_id}")


async def concurrent_logging_example():
    """Example showing concurrent logging for high throughput."""
    print("\n=== Concurrent Logging Example ===")

    async with ziz.AsyncClient(
        api_key="your-secret-key-change-in-production",
        feature_id="high-throughput",
        api_url="http://localhost:8000",
        batch_size=10,
    ) as client:

        async def log_single_output(index: int) -> str:
            """Log a single output with simulated processing time."""
            # Simulate some async work
            await asyncio.sleep(0.1)

            output_id = await client.log_output(
                content=f"Concurrent output #{index}",
                metadata={
                    "index": index,
                    "worker": "async_worker",
                    "timestamp": time.time(),
                },
            )

            print(f"Worker {index} logged: {output_id}")
            return output_id

        # Launch multiple concurrent tasks
        print("Starting 20 concurrent logging tasks...")
        start_time = time.time()

        tasks = [log_single_output(i) for i in range(20)]
        output_ids = await asyncio.gather(*tasks)

        end_time = time.time()
        print(
            f"Completed {len(output_ids)} outputs in {end_time - start_time:.2f} seconds"
        )

        # Log interactions for all outputs concurrently
        async def log_feedback(output_id: str, feedback: str) -> str:
            return await client.log_interaction(
                type="feedback", value=feedback, output_id=output_id
            )

        print("Logging feedback for all outputs...")
        feedback_tasks = [
            log_feedback(output_id, "positive" if i % 2 == 0 else "negative")
            for i, output_id in enumerate(output_ids)
        ]

        feedback_ids = await asyncio.gather(*feedback_tasks)
        print(f"Logged {len(feedback_ids)} feedback interactions")


async def async_context_manager_example():
    """Example showing async context manager usage."""
    print("\n=== Async Context Manager Example ===")

    client = ziz.AsyncClient(
        api_key="your-secret-key-change-in-production",
        feature_id="async-generation",
        api_url="http://localhost:8000",
    )

    try:
        # Use async context manager for tracking
        async with ziz.atrack_output(
            client, metadata={"framework": "async"}
        ) as tracker:
            # Simulate async AI generation
            await asyncio.sleep(0.5)  # Simulate processing time

            generated_text = "Async generated content with complex processing"
            tracker.set_content(generated_text)
            tracker.add_metadata("processing_time", 0.5)

            # Add async interactions
            tracker.thumbs_up()
            tracker.custom("processing_complete", True)

        print("Async context manager tracking completed")

    finally:
        await client.aclose()


async def async_decorator_example():
    """Example showing async decorator usage."""
    print("\n=== Async Decorator Example ===")

    client = ziz.AsyncClient(
        api_key="your-secret-key-change-in-production",
        feature_id="async-translation",
        api_url="http://localhost:8000",
    )

    try:
        # Decorate an async function
        @ziz.async_track_output(
            client,
            content_extractor=lambda result: result["translation"],
            metadata_extractor=lambda args, result: {
                "source_text_length": len(args["text"]),
                "target_language": args["target_lang"],
                "confidence": result["confidence"],
            },
        )
        async def async_translate(text: str, target_lang: str):
            """Simulated async translation function."""
            # Simulate async API call
            await asyncio.sleep(0.2)

            return {
                "translation": f"[{target_lang.upper()}] {text}",
                "confidence": 0.92,
                "processing_time": 0.2,
            }

        # Use the decorated async function
        result = await async_translate("Hello async world", "es")
        print(f"Async translation: {result}")

    finally:
        await client.aclose()


async def async_error_handling_example():
    """Example showing async error handling."""
    print("\n=== Async Error Handling Example ===")

    # Client with strict mode disabled
    client = ziz.AsyncClient(
        api_key="your-secret-key-change-in-production",
        feature_id="async-errors",
        api_url="http://localhost:8000",
        strict_mode=False,
    )

    try:

        async def potentially_failing_operation():
            """Simulate an operation that might fail."""
            import random

            if random.random() < 0.3:  # 30% chance of failure
                raise ValueError("Simulated async error")

            return "Success!"

        # Run multiple operations, some may fail
        tasks = []
        for i in range(10):

            async def log_with_error_handling(index: int):
                try:
                    result = await potentially_failing_operation()

                    output_id = await client.log_output(
                        content=result,
                        metadata={"operation_index": index, "status": "success"},
                    )
                    print(f"Operation {index} succeeded: {output_id}")
                    return output_id

                except Exception as e:
                    # Log the error as an output
                    error_output_id = await client.log_output(
                        content=str(e),
                        metadata={
                            "operation_index": index,
                            "status": "error",
                            "error_type": type(e).__name__,
                        },
                    )
                    print(f"Operation {index} failed, logged error: {error_output_id}")
                    return error_output_id

            tasks.append(log_with_error_handling(i))

        # Wait for all operations to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if not isinstance(r, Exception))
        print(f"Completed {len(results)} operations, {success_count} succeeded")

    finally:
        await client.aclose()


async def async_batch_streaming_example():
    """Example showing streaming and batch processing."""
    print("\n=== Async Batch Streaming Example ===")

    client = ziz.AsyncClient(
        api_key="your-secret-key-change-in-production",
        feature_id="streaming",
        api_url="http://localhost:8000",
        batch_size=5,
        batch_timeout=1.0,
    )

    try:

        async def simulate_streaming_responses():
            """Simulate streaming AI responses."""
            for i in range(15):
                # Simulate streaming response chunks
                chunk = f"Response chunk #{i} with streaming data"

                output_id = await client.log_output(
                    content=chunk,
                    metadata={
                        "chunk_index": i,
                        "streaming": True,
                        "timestamp": time.time(),
                    },
                )

                print(f"Streamed chunk {i}: {output_id}")

                # Simulate real-time streaming delay
                await asyncio.sleep(0.3)

                # Occasionally log interactions
                if i % 3 == 0:
                    await client.log_interaction(
                        type="stream_event",
                        value="chunk_received",
                        output_id=output_id,
                        metadata={"chunk_number": i},
                    )

        await simulate_streaming_responses()

        # Force flush any remaining events
        await client.aflush()
        print("Streaming simulation completed")

    finally:
        await client.aclose()


async def async_microservice_example():
    """Example showing async microservice communication."""
    print("\n=== Async Microservice Example ===")

    async def service_a_async():
        """Async service that generates outputs."""
        async with ziz.AsyncClient(
            api_key="your-secret-key-change-in-production",
            feature_id="async-microservice-a",
            api_url="http://localhost:8000",
        ) as client:
            output_id = await client.log_output(
                content="Async microservice A output",
                metadata={
                    "service": "service_a",
                    "async": True,
                    "timestamp": time.time(),
                },
            )

            print(f"Service A (async) output: {output_id}")
            return output_id

    async def service_b_async(output_id: str):
        """Async service that processes outputs from service A."""
        async with ziz.AsyncClient(
            api_key="your-secret-key-change-in-production",
            feature_id="async-microservice-b",
            api_url="http://localhost:8000",
        ) as client:
            # Log interaction with the output from service A
            interaction_id = await client.log_interaction(
                output_id=output_id,
                type="processing",
                value="processed_by_service_b",
                metadata={
                    "service": "service_b",
                    "async": True,
                    "processing_time": 0.1,
                },
            )

            print(f"Service B (async) interaction: {interaction_id}")
            return interaction_id

    async def service_c_async(output_id: str):
        """Async service that adds final interactions."""
        async with ziz.AsyncClient(
            api_key="your-secret-key-change-in-production",
            feature_id="async-microservice-c",
            api_url="http://localhost:8000",
        ) as client:
            interaction_id = await client.log_interaction(
                output_id=output_id,
                type="finalization",
                value="completed",
                metadata={"service": "service_c", "async": True, "final_step": True},
            )

            print(f"Service C (async) interaction: {interaction_id}")
            return interaction_id

    # Run services concurrently where possible
    output_id = await service_a_async()

    # Services B and C can process the same output concurrently
    service_b_task = service_b_async(output_id)
    service_c_task = service_c_async(output_id)

    await asyncio.gather(service_b_task, service_c_task)
    print("Async microservice workflow completed")


async def performance_comparison_example():
    """Example comparing sync vs async performance."""
    print("\n=== Performance Comparison Example ===")

    # Async version
    async def async_performance_test():
        async with ziz.AsyncClient(
            api_key="your-secret-key-change-in-production",
            feature_id="async-performance",
            api_url="http://localhost:8000",
            batch_size=20,
        ) as client:
            start_time = time.time()

            async def log_async_output(i):
                return await client.log_output(
                    content=f"Async performance test #{i}",
                    metadata={"test": "async", "index": i},
                )

            # Log 50 outputs concurrently
            tasks = [log_async_output(i) for i in range(50)]
            await asyncio.gather(*tasks)

            end_time = time.time()
            return end_time - start_time

    # Sync version for comparison
    def sync_performance_test():
        client = ziz.Client(
            api_key="your-secret-key-change-in-production",
            feature_id="sync-performance",
            api_url="http://localhost:8000",
            batch_size=20,
        )

        try:
            start_time = time.time()

            # Log 50 outputs sequentially
            for i in range(50):
                client.log_output(
                    content=f"Sync performance test #{i}",
                    metadata={"test": "sync", "index": i},
                )

            end_time = time.time()
            return end_time - start_time
        finally:
            client.cleanup()

    # Run performance tests
    print("Running async performance test...")
    async_time = await async_performance_test()
    print(f"Async test completed in {async_time:.2f} seconds")

    print("Running sync performance test...")
    sync_time = sync_performance_test()
    print(f"Sync test completed in {sync_time:.2f} seconds")

    speedup = sync_time / async_time if async_time > 0 else float("inf")
    print(f"Async was {speedup:.2f}x faster than sync")


async def main():
    """Run all async examples."""
    print("Ziz SDK Async Examples")
    print("======================")
    print("Make sure your Ziz API is running on http://localhost:8000")
    print()

    try:
        await basic_async_example()
        await concurrent_logging_example()
        await async_context_manager_example()
        await async_decorator_example()
        await async_error_handling_example()
        await async_batch_streaming_example()
        await async_microservice_example()
        await performance_comparison_example()

        print("\n✅ All async examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Async example failed: {e}")
        print("Make sure your Ziz API is running and accessible.")


if __name__ == "__main__":
    asyncio.run(main())
