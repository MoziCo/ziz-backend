# Ziz SDK Requirements

This document defines requirements for the **Ziz SDKs** (Python, JavaScript) that provide a low-friction way to log outputs and interactions into the Ziz API.

---

## Core Goals

* **Minimal developer effort** – One-line setup, minimal code changes
* **Consistent interface** – Same concepts across Python & JS
* **Resilient** – Batching, retries, idempotency support
* **Privacy-first** – Redaction and safe defaults

---

## Key Concepts

* **Feature** (`feature_id`) – Application feature under evaluation
* **Output** – Generated result to evaluate (e.g., model response)
* **Interaction** – User/system event linked to an output

---

## SDK Structure

### Initialization

```python
import ziz
client = ziz.Client(api_key="...", feature_id="chatbot-v1")
```

* Config via constructor or env vars (`ZIZ_API_KEY`, `ZIZ_API_URL`)
* Default `feature_id` can be set globally

### Logging Outputs

```python
output_id = client.log_output(
    content="Model reply text",
    metadata={"model":"gpt-4","latency_ms":1200}
)
```

* Returns `output_id` (generated if not provided)

### Logging Interactions

```python
client.log_interaction(
    output_id=output_id,
    type="feedback",
    value="thumbs_up"
)
```

* Supports multiple interactions per output
* Attaches automatically to last output if not provided

### Context Managers / Decorators

```python
with client.track_output(metadata={"model":"gpt-4"}) as out:
    out.set_content(run_model())
    out.add_interaction(type="feedback", value="thumbs_up")
```

* Simplifies integration with existing code

---

## Microservice Usage Examples

### Example 1 – Separate Services (1 → many)

#### Service A – Output Generator

```python
# service_a.py
client = ziz.Client(api_key="...", feature_id="chatbot-v1")

output_id = client.log_output(
    content="Hello from the model!",
    metadata={"model":"gpt-4"}
)

# Output_id is returned and can be shared with Service B
print(output_id)
```

#### Service B – Interaction Logger

```python
# service_b.py
client = ziz.Client(api_key="...", feature_id="chatbot-v1")

client.log_interaction(
    output_id="out-12345",
    type="feedback",
    value="thumbs_down",
    metadata={"user_id":"user-42"}
)
```

* Interactions are correctly linked to the output across services
* Multiple interactions can be logged for the same output

### Example 2 – Developer Enforces `output_id`

```python
client = ziz.Client(api_key="...", feature_id="chatbot-v1")

# Developer enforces custom output_id
client.log_output(
    output_id="out-99999",
    content="Forced ID output",
    metadata={"model":"gpt-4"}
)
```

### Behavior on `output_id` Reuse

* **Idempotent behavior:** If the same output is resent with identical payload → ignored by server.
* **Conflict:** If the same `output_id` is reused with different content → server responds with **409 Conflict** and returns the existing record.
* **Result:** Safe retries allowed, accidental overwrites prevented.

---

## Technical Requirements

1. **Batching**

   * Collect events in memory; flush on size or interval
   * Flush on program exit

2. **Retries & Idempotency**

   * Retries on 5xx/429 with exponential backoff
   * Use `client_event_id` and `Idempotency-Key`

3. **Async Support**

   * Async methods (`await client.log_output(...)`)
   * Background thread/worker for Python

4. **Privacy & Redaction**

   * Redaction enabled by default (no prompt/completion content)
   * Opt-in via `allow_content=True`

5. **Error Handling**

   * Non-blocking: errors logged via SDK logger, not raised by default
   * Option to enable strict mode (raise exceptions)

6. **Extensibility**

   * Custom interaction types (`type="custom"`)
   * Arbitrary metadata key/values

---

## Deliverables (MVP)

* Python SDK (sync + async)
* JavaScript SDK (Node + browser)
* Shared concepts: Feature, Output, Interaction
* Config via env vars + client init
* Output + Interaction logging APIs
* Batching, retries, redaction

Later: decorators/context managers, automatic framework integrations, tracing hooks.
