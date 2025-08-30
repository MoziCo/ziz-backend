"""
Function decorators for the Ziz SDK.

Provides decorators for automatic output tracking and logging.
"""

import functools
import inspect
from typing import Any, Callable, Dict, Optional, TypeVar

from ..client.base import BaseClient
from ..utils import get_logger

logger = get_logger("decorators")

F = TypeVar("F", bound=Callable[..., Any])


def track_output(
    client: BaseClient,
    feature_id: Optional[str] = None,
    content_extractor: Optional[Callable[[Any], Any]] = None,
    metadata_extractor: Optional[Callable[[Any, Any], Dict[str, Any]]] = None,
    capture_args: bool = False,
    capture_kwargs: bool = False,
    exclude_args: Optional[list] = None,
    include_execution_time: bool = True,
):
    """
    Decorator to automatically track function outputs.

    Args:
        client: Ziz client instance
        feature_id: Feature ID (uses client default if not provided)
        content_extractor: Function to extract content from return value
        metadata_extractor: Function to extract metadata from args and return value
        capture_args: Whether to capture function arguments as metadata
        capture_kwargs: Whether to capture function keyword arguments as metadata
        exclude_args: List of argument names to exclude from metadata
        include_execution_time: Whether to include execution time in metadata

    Usage:
        @track_output(client, feature_id="my-feature")
        def generate_text(prompt):
            return model.generate(prompt)

        @track_output(
            client,
            content_extractor=lambda result: result.text,
            metadata_extractor=lambda args, result: {"tokens": result.token_count}
        )
        def complex_generation(prompt, temperature=0.7):
            return model.generate(prompt, temperature=temperature)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Extract content
                if content_extractor:
                    content = content_extractor(result)
                else:
                    content = result

                # Build metadata
                metadata = {}

                if include_execution_time:
                    execution_time = time.time() - start_time
                    metadata["execution_time"] = execution_time

                # Capture function arguments
                if capture_args or capture_kwargs:
                    sig = inspect.signature(func)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()

                    exclude_set = set(exclude_args or [])

                    if capture_args:
                        for name, value in bound_args.arguments.items():
                            if name not in exclude_set:
                                metadata[f"arg_{name}"] = value

                # Extract custom metadata
                if metadata_extractor:
                    custom_metadata = metadata_extractor(
                        bound_args.arguments if capture_args else args, result
                    )
                    if custom_metadata:
                        metadata.update(custom_metadata)

                # Log the output
                output_id = client.log_output(
                    content=content, feature_id=feature_id, metadata=metadata
                )

                if output_id:
                    logger.debug(
                        f"Tracked output {output_id} for function {func.__name__}"
                    )

                return result

            except Exception as e:
                # Log error as metadata if execution fails
                if include_execution_time:
                    execution_time = time.time() - start_time

                error_output_id = client.log_output(
                    content=str(e),
                    feature_id=feature_id,
                    metadata={
                        "error": True,
                        "error_type": type(e).__name__,
                        "execution_time": execution_time
                        if include_execution_time
                        else None,
                        "function": func.__name__,
                    },
                )

                if error_output_id:
                    logger.debug(
                        f"Tracked error output {error_output_id} for function {func.__name__}"
                    )

                # Re-raise the exception
                raise

        return wrapper

    return decorator


def track_function(
    client: BaseClient,
    feature_id: Optional[str] = None,
    track_calls: bool = True,
    track_results: bool = True,
    track_errors: bool = True,
    include_args: bool = False,
    exclude_args: Optional[list] = None,
):
    """
    Decorator to track function calls, results, and errors as separate outputs.

    Args:
        client: Ziz client instance
        feature_id: Feature ID (uses client default if not provided)
        track_calls: Whether to track function calls
        track_results: Whether to track function results
        track_errors: Whether to track function errors
        include_args: Whether to include function arguments in metadata
        exclude_args: List of argument names to exclude

    Usage:
        @track_function(client, feature_id="api-calls")
        def api_call(endpoint, data):
            return requests.post(endpoint, json=data)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            # Build common metadata
            metadata = {
                "function": func.__name__,
                "module": func.__module__,
            }

            if include_args:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                exclude_set = set(exclude_args or [])

                for name, value in bound_args.arguments.items():
                    if name not in exclude_set:
                        metadata[f"arg_{name}"] = value

            # Track function call
            call_output_id = None
            if track_calls:
                call_output_id = client.log_output(
                    content=f"Function call: {func.__name__}",
                    feature_id=feature_id,
                    metadata={**metadata, "event_type": "call"},
                )

                if call_output_id:
                    logger.debug(f"Tracked function call {call_output_id}")

            try:
                # Execute the function
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Track successful result
                if track_results:
                    result_metadata = {
                        **metadata,
                        "event_type": "result",
                        "execution_time": execution_time,
                        "success": True,
                    }

                    if call_output_id:
                        result_metadata["call_output_id"] = call_output_id

                    result_output_id = client.log_output(
                        content=result, feature_id=feature_id, metadata=result_metadata
                    )

                    if result_output_id:
                        logger.debug(f"Tracked function result {result_output_id}")

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                # Track error
                if track_errors:
                    error_metadata = {
                        **metadata,
                        "event_type": "error",
                        "execution_time": execution_time,
                        "success": False,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    }

                    if call_output_id:
                        error_metadata["call_output_id"] = call_output_id

                    error_output_id = client.log_output(
                        content=f"Error in {func.__name__}: {str(e)}",
                        feature_id=feature_id,
                        metadata=error_metadata,
                    )

                    if error_output_id:
                        logger.debug(f"Tracked function error {error_output_id}")

                # Re-raise the exception
                raise

        return wrapper

    return decorator


def async_track_output(
    client: BaseClient,
    feature_id: Optional[str] = None,
    content_extractor: Optional[Callable[[Any], Any]] = None,
    metadata_extractor: Optional[Callable[[Any, Any], Dict[str, Any]]] = None,
    capture_args: bool = False,
    capture_kwargs: bool = False,
    exclude_args: Optional[list] = None,
    include_execution_time: bool = True,
):
    """
    Async version of track_output decorator.

    Usage:
        @async_track_output(client, feature_id="async-feature")
        async def generate_text_async(prompt):
            return await model.generate_async(prompt)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                # Execute the async function
                result = await func(*args, **kwargs)

                # Extract content
                if content_extractor:
                    content = content_extractor(result)
                else:
                    content = result

                # Build metadata
                metadata = {}

                if include_execution_time:
                    execution_time = time.time() - start_time
                    metadata["execution_time"] = execution_time

                # Capture function arguments
                if capture_args or capture_kwargs:
                    sig = inspect.signature(func)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()

                    exclude_set = set(exclude_args or [])

                    if capture_args:
                        for name, value in bound_args.arguments.items():
                            if name not in exclude_set:
                                metadata[f"arg_{name}"] = value

                # Extract custom metadata
                if metadata_extractor:
                    custom_metadata = metadata_extractor(
                        bound_args.arguments if capture_args else args, result
                    )
                    if custom_metadata:
                        metadata.update(custom_metadata)

                # Log the output (check if client has async method)
                if hasattr(client, "log_output") and hasattr(
                    client.log_output, "__await__"
                ):
                    output_id = await client.log_output(
                        content=content, feature_id=feature_id, metadata=metadata
                    )
                else:
                    output_id = client.log_output(
                        content=content, feature_id=feature_id, metadata=metadata
                    )

                if output_id:
                    logger.debug(
                        f"Tracked async output {output_id} for function {func.__name__}"
                    )

                return result

            except Exception as e:
                # Log error as metadata if execution fails
                if include_execution_time:
                    execution_time = time.time() - start_time

                error_metadata = {
                    "error": True,
                    "error_type": type(e).__name__,
                    "execution_time": execution_time
                    if include_execution_time
                    else None,
                    "function": func.__name__,
                }

                # Log error output
                if hasattr(client, "log_output") and hasattr(
                    client.log_output, "__await__"
                ):
                    error_output_id = await client.log_output(
                        content=str(e), feature_id=feature_id, metadata=error_metadata
                    )
                else:
                    error_output_id = client.log_output(
                        content=str(e), feature_id=feature_id, metadata=error_metadata
                    )

                if error_output_id:
                    logger.debug(
                        f"Tracked async error output {error_output_id} for function {func.__name__}"
                    )

                # Re-raise the exception
                raise

        return wrapper

    return decorator
