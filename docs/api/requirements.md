# Ziz API Requirements (Revised)

This document defines the **API requirements** for Ziz, focusing on the ingestion layer (API + SDK) that collects **outputs** and **interactions** for later analysis.

---

## Core Concepts

* **Feature (`feature_id`)**: The main container for evaluation. Each feature groups outputs and their related interactions.
* **Output**: A system-generated result (e.g., GenAI response, recommendation, prediction). Each output belongs to exactly one feature.
* **Interaction**: A user or system action related to an output (feedback, annotation, edit, click, etc.). Multiple interactions can be attached to a single output.
* **1→Many Relationship**: Each output can have many interactions, connected by the `output_id`.

---

## API Principles

* **Stateless** REST API (JSON over HTTPS)
* **Authentication**: API key per product/application
* **Versioning**: URI-based (`/v1/...`)
* **Idempotency**: All create endpoints accept client-provided IDs
* **Minimal Friction**: Simple payloads, easy to extend

---

## Data Model (Simplified JSON)

### Feature

```json
{
  "feature_id": "uuid-or-client-id",
  "name": "Chatbot QA",
  "metadata": {"team": "NLP"}
}
```

### Output

```json
{
  "output_id": "uuid-or-client-id",
  "feature_id": "feature-123",
  "content": "Model generated text here", // Support Any structure as content, not just text
  "metadata": {"model": "gpt-4", "prompt": "..."},
  "timestamp": "2025-08-19T10:00:00Z"
}
```

### Interaction

```json
{
  "interaction_id": "uuid-or-client-id",
  "output_id": "output-123",
  "type": "feedback|edit|click|custom",
  "value": "thumbs_up", // Support Any structure as content, not just text
  "metadata": {"user_id": "u-1", "latency_ms": 200},
  "timestamp": "2025-08-19T10:05:00Z"
}
```

**NOTE**: In the analysis phase, interactions are transformed into derived features of outputs, providing the behavioral signals used in satisfaction prediction and feature discovery

---

## API Endpoints

### Features

* `POST /v1/features` – Create feature (id optional, returned if not provided)
* `GET /v1/features/{feature_id}` – Get feature
* `GET /v1/features` – List features

### Outputs

* `POST /v1/outputs` – Create output (requires `feature_id`)
* `GET /v1/outputs/{output_id}` – Get output
* `GET /v1/features/{feature_id}/outputs` – List outputs for a feature

### Interactions

* `POST /v1/interactions` – Create interaction (requires `output_id`)
* `GET /v1/interactions/{interaction_id}` – Get interaction
* `GET /v1/outputs/{output_id}/interactions` – List interactions for output

### Batch Support

* `POST /v1/outputs/batch` – Bulk upload outputs
* `POST /v1/interactions/batch` – Bulk upload interactions

---

## Basic Flow

1. **Feature Creation** – App defines a feature via `POST /features` (or reuses existing `feature_id`).
2. **Upload Output** – App sends generated result to `POST /outputs`. Response includes `output_id`.
3. **Attach Interactions** – Later, app (or SDK) sends related events to `POST /interactions` with that `output_id`.
4. **Query** – Client retrieves outputs + interactions for analysis (`GET /features/{id}/outputs`).

---

## Example Flow (cURL)

```bash
# Create feature
curl -X POST https://api.ziz.ai/v1/features \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"feature_id":"chatbot-v1", "name":"Chatbot QA"}'

# Upload output
curl -X POST https://api.ziz.ai/v1/outputs \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"feature_id":"chatbot-v1","output_id":"o1","content":"Hello!"}'

# Add interaction
curl -X POST https://api.ziz.ai/v1/interactions \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"output_id":"o1","interaction_id":"i1","type":"feedback","value":"thumbs_up"}'
```

---

## SDK Expectations

* Thin wrapper over REST API
* Provide decorators/context managers for auto-logging
* Async + batch support
* Env-var based config (`ZIZ_API_KEY`, `ZIZ_API_URL`)

---

## MVP Scope

* Feature, Output, Interaction endpoints
* Idempotent creation with client IDs
* Batch ingestion support
* Basic metadata and timestamps
* Auth with API key
* Persist all the information in mongodb collection

Future phases will add **analysis, dashboards, recommendations, and experiment flows**.

---

## Provision Requirements

Prepare the API to pass the outputs and interactions to message-broker systems. Those systems will then better handle the analysis.
To achieve this provision, make sure that the persistence layer is decoupled from the API. (e.g. the API uses a single function for storing the data. That function can be replaced with "send message" in the future).
