# Ziz Python SDK

The Ziz SDK provides a simple, powerful interface for logging outputs and interactions from your AI applications for evaluation and analysis.

## ✨ Features

- **🚀 High Performance**: Automatic batching and async support
- **🔒 Privacy First**: Configurable content redaction and safe defaults
- **🔄 Resilient**: Automatic retries with exponential backoff
- **⚡ Easy Integration**: One-line setup with decorators and context managers
- **🎯 Flexible**: Support for custom interaction types and metadata
- **🔗 Idempotent**: Built-in support for safe retries and duplicate prevention
- **📊 Framework Agnostic**: Works with OpenAI, LangChain, Hugging Face, and more

## 🚀 Quick Start

### Installation

```bash
pip install ziz
```

### Basic Usage

```python
import ziz

# Initialize client
client = ziz.Client(api_key="your-api-key", feature_id="chatbot-v1")

# Log an output
output_id = client.log_output(
    "Hello! How can I help you today?",
    metadata={"model": "gpt-4", "temperature": 0.7}
)

# Log user feedback
client.log_interaction("feedback", "thumbs_up", output_id=output_id)

# Cleanup (optional - happens automatically)
client.cleanup()
```

### Async Usage

```python
import ziz
import asyncio

async def main():
    async with ziz.AsyncClient(api_key="your-api-key", feature_id="chatbot-v1") as client:
        output_id = await client.log_output("Async response")
        await client.log_interaction("feedback", "positive", output_id=output_id)

asyncio.run(main())
```

## 📖 Configuration

### Environment Variables

The SDK automatically picks up configuration from environment variables:

```bash
export ZIZ_API_KEY="your-api-key"
export ZIZ_API_URL="https://api.ziz.ai"
export ZIZ_FEATURE_ID="your-default-feature"
export ZIZ_BATCH_SIZE="100"
export ZIZ_BATCH_TIMEOUT="5.0"
export ZIZ_ALLOW_CONTENT="false"  # Privacy setting
export ZIZ_STRICT_MODE="false"    # Error handling
```

### Programmatic Configuration

```python
import ziz

# Direct configuration
client = ziz.Client(
    api_key="your-api-key",
    api_url="https://api.ziz.ai",
    feature_id="my-feature",
    batch_size=50,
    batch_timeout=2.0,
    allow_content=True,
    strict_mode=False
)

# Using ZizConfig object
config = ziz.ZizConfig(
    api_key="your-api-key",
    feature_id="my-feature",
    allow_content=True
)
client = ziz.Client(config=config)
```

## 🛠️ Advanced Usage

### Context Managers

```python
with client.track_output(metadata={"model": "gpt-4"}) as tracker:
    result = run_model()
    tracker.set_content(result)
    tracker.thumbs_up()
    tracker.add_interaction("edit", "corrected_text")
```

### Function Decorators

```python
@ziz.track_output(
    client,
    content_extractor=lambda result: result.text,
    metadata_extractor=lambda args, result: {"tokens": result.token_count}
)
def generate_text(prompt):
    return model.generate(prompt)

result = generate_text("Write a story")  # Automatically logged
```

### Async Context Managers

```python
async with ziz.atrack_output(client, metadata={"async": True}) as tracker:
    result = await async_model_call()
    tracker.set_content(result)
    tracker.feedback("positive")
```

### Batch Processing

```python
# High-throughput scenario
client = ziz.Client(
    api_key="your-api-key",
    feature_id="batch-processing",
    batch_size=100,      # Flush after 100 events
    batch_timeout=5.0    # Or after 5 seconds
)

# Log many outputs - they'll be batched automatically
for i in range(1000):
    client.log_output(f"Output #{i}")

# Force flush remaining events
client.flush()
```

## 🔒 Privacy & Security

### Content Redaction

By default, the SDK redacts sensitive content for privacy:

```python
# Privacy-first (default)
client = ziz.Client(api_key="key", allow_content=False)
client.log_output("Email: user@example.com")  # Email will be redacted

# Opt-in to content logging
client = ziz.Client(api_key="key", allow_content=True)
client.log_output("This content will be logged as-is")
```

### Custom Redaction Rules

```python
from ziz.utils import RedactionManager, RedactionRule

# Add custom redaction
redactor = RedactionManager()
redactor.add_rule(RedactionRule(r'\bpassword:\s*\w+', '[PASSWORD]'))

client = ziz.Client(api_key="key")
client.redaction_manager = redactor
```

## 🔄 Error Handling & Resilience

### Automatic Retries

```python
client = ziz.Client(
    api_key="your-api-key",
    retry_attempts=3,     # Retry up to 3 times
    retry_delay=1.0,      # Starting delay
    strict_mode=False     # Don't raise exceptions
)
```

### Strict vs Non-Strict Mode

```python
# Non-strict mode (default): Errors are logged but not raised
client = ziz.Client(api_key="key", strict_mode=False)
result = client.log_output("content")  # Returns None on error

# Strict mode: Errors are raised as exceptions
client = ziz.Client(api_key="key", strict_mode=True)
try:
    result = client.log_output("content")
except Exception as e:
    print(f"Logging failed: {e}")
```

## 🔗 Framework Integrations

### OpenAI Integration

```python
import openai
import ziz

client = ziz.Client(api_key="ziz-key", feature_id="openai-chat")

def chat_with_logging(messages, model="gpt-4"):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages
    )

    # Log to Ziz
    output_id = client.log_output(
        content=response.choices[0].message.content,
        metadata={
            "model": model,
            "tokens": response.usage.total_tokens,
            "openai_id": response.id
        }
    )

    return response, output_id
```

### LangChain Integration

```python
from langchain import LLMChain
import ziz

client = ziz.Client(api_key="ziz-key", feature_id="langchain")

@ziz.track_output(client)
def run_chain(chain, input_text):
    return chain.run(input_text)

# Usage
chain = LLMChain(...)
result = run_chain(chain, "input")  # Automatically logged
```

### FastAPI Integration

```python
from fastapi import FastAPI
import ziz

app = FastAPI()
client = ziz.Client(api_key="ziz-key", feature_id="api")

@app.post("/predict")
async def predict(request: PredictRequest):
    result = await model.predict(request.text)

    # Log prediction
    output_id = await client.log_output(
        content=result,
        metadata={
            "endpoint": "/predict",
            "user_id": request.user_id
        }
    )

    return {"result": result, "output_id": output_id}

@app.post("/feedback")
async def feedback(request: FeedbackRequest):
    await client.log_interaction(
        type="feedback",
        value=request.feedback,
        output_id=request.output_id
    )
    return {"status": "logged"}
```

## 📊 Monitoring & Observability

### Check Batch Status

```python
# Check pending events
pending_count = client.get_pending_count()
print(f"Pending events: {pending_count}")

# Check if batch is empty
is_empty = client.is_batch_empty()
print(f"Batch empty: {is_empty}")
```

### Last Output Tracking

```python
# The SDK tracks the last output ID for convenience
client.log_output("First output")
print(f"Last output: {client.last_output_id}")

# Use with interactions
client.log_interaction("feedback", "good")  # Uses last output ID automatically
```

## 🎯 Best Practices

### 1. Use Environment Variables

```python
# ✅ Good: Use environment variables
client = ziz.Client()  # Picks up ZIZ_API_KEY automatically

# ❌ Avoid: Hardcoding API keys
client = ziz.Client(api_key="hardcoded-key")
```

### 2. Set Default Feature ID

```python
# ✅ Good: Set default feature ID
client = ziz.Client(feature_id="my-app")
client.log_output("content")  # Uses default feature ID

# ❌ Avoid: Repeating feature ID
client.log_output("content", feature_id="my-app")
client.log_output("content", feature_id="my-app")
```

### 3. Use Context Managers for Complex Workflows

```python
# ✅ Good: Use context managers for complex logging
with client.track_output() as tracker:
    result = complex_ai_operation()
    tracker.set_content(result)
    tracker.add_metadata("complexity", "high")
    if user_liked_result:
        tracker.thumbs_up()

# ❌ Avoid: Manual tracking with multiple steps
output_id = client.log_output(result)
client.log_interaction("metadata", {"complexity": "high"}, output_id)
if user_liked_result:
    client.log_interaction("feedback", "thumbs_up", output_id)
```

### 4. Handle Errors Gracefully

```python
# ✅ Good: Use non-strict mode for resilience
client = ziz.Client(strict_mode=False)
output_id = client.log_output("content")  # Won't crash on network issues

# ✅ Good: Use strict mode with proper error handling
client = ziz.Client(strict_mode=True)
try:
    output_id = client.log_output("content")
except Exception as e:
    logger.error(f"Failed to log to Ziz: {e}")
```

### 5. Optimize for High Throughput

```python
# ✅ Good: Configure batching for high throughput
client = ziz.Client(
    batch_size=100,      # Larger batches
    batch_timeout=10.0   # Longer timeout
)

# ✅ Good: Use async for concurrent operations
async with ziz.AsyncClient() as client:
    tasks = [client.log_output(f"output {i}") for i in range(100)]
    await asyncio.gather(*tasks)
```

## 🛟 Troubleshooting

### Common Issues

1. **"API key is required" Error**

   ```python
   # Set API key via environment or parameter
   export ZIZ_API_KEY="your-api-key"
   # OR
   client = ziz.Client(api_key="your-api-key")
   ```

2. **Network Connection Issues**

   ```python
   # Use non-strict mode and check retry settings
   client = ziz.Client(
       strict_mode=False,
       retry_attempts=5,
       retry_delay=2.0
   )
   ```

3. **High Memory Usage**

   ```python
   # Reduce batch size and timeout
   client = ziz.Client(
       batch_size=10,      # Smaller batches
       batch_timeout=1.0   # Faster flushing
   )
   ```

4. **Content Not Appearing**

   ```python
   # Check content redaction settings
   client = ziz.Client(allow_content=True)  # Enable content logging
   ```

### Enable Debug Logging

```python
import logging
logging.getLogger("ziz").setLevel(logging.DEBUG)
```

## 📚 API Reference

### Client Classes

- `ziz.Client` - Synchronous client
- `ziz.AsyncClient` - Asynchronous client
- `ziz.ZizConfig` - Configuration object

### Core Methods

- `log_output(content, metadata=None, ...)` - Log an output
- `log_interaction(type, value, output_id=None, ...)` - Log an interaction
- `flush()` - Flush pending events
- `cleanup()` - Clean up resources

### Convenience Methods

- `feedback(value, output_id=None)` - Log feedback
- `thumbs_up(output_id=None)` - Log positive feedback
- `thumbs_down(output_id=None)` - Log negative feedback

### Context Manager Functions

- `track_output()` - Track output with interactions
- `atrack_output()` - Async version of track_output

### Decorators

- `@track_output()` - Automatically track function outputs
- `@track_function()` - Track function calls, results, and errors
- `@async_track_output()` - Async version of track_output

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](../CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.ziz.ai](https://docs.ziz.ai)
- **Issues**: [GitHub Issues](https://github.com/your-org/ziz/issues)
- **Discord**: [Join our community](https://discord.gg/ziz)
- **Email**: <support@ziz.ai>

---

Made with ❤️ by the Ziz team
