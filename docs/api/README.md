# Ziz API Implementation

This document provides information about the implemented Ziz API based on the requirements.

## Features Implemented

✅ **Complete API Implementation** following the requirements specification:

### Core Endpoints

- `POST /v1/features` - Create feature (with optional client-provided ID)
- `GET /v1/features/{feature_id}` - Get feature by ID
- `GET /v1/features` - List features with pagination
- `PUT /v1/features/{feature_id}` - Update feature

- `POST /v1/outputs` - Create output (requires feature_id)
- `GET /v1/outputs/{output_id}` - Get output by ID
- `GET /v1/features/{feature_id}/outputs` - List outputs for feature
- `PUT /v1/outputs/{output_id}` - Update output

- `POST /v1/interactions` - Create interaction (requires output_id)
- `GET /v1/interactions/{interaction_id}` - Get interaction by ID
- `GET /v1/outputs/{output_id}/interactions` - List interactions for output
- `PUT /v1/interactions/{interaction_id}` - Update interaction

### Batch Endpoints

- `POST /v1/outputs/batch` - Bulk create outputs
- `POST /v1/interactions/batch` - Bulk create interactions

### System Endpoints

- `GET /` - Root endpoint with basic info
- `GET /health` - Health check with database status
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

## Architecture

The implementation follows clean architecture principles with proper separation of concerns:

### Layer Structure

```bash
┌─────────────────────────────────────┐
│           API Routes                │  ← FastAPI routers, request/response handling
├─────────────────────────────────────┤
│         Business Logic              │  ← Services with validation and business rules
├─────────────────────────────────────┤
│        Storage Interface            │  ← Abstract storage layer (future message broker)
├─────────────────────────────────────┤
│         Repository Layer            │  ← Database access patterns
├─────────────────────────────────────┤
│         Database Layer              │  ← MongoDB connection and indexing
└─────────────────────────────────────┘
```

### Key Design Decisions

1. **Decoupled Storage**: Storage service interface allows easy replacement with message brokers
2. **Repository Pattern**: Abstracts database operations for better testability
3. **Comprehensive Validation**: Pydantic models for request/response validation
4. **API Key Authentication**: Simple and effective authentication mechanism
5. **Error Handling**: Centralized exception handling with proper HTTP status codes
6. **Configuration Management**: Environment-based configuration with sensible defaults

## Usage Examples

### Authentication

All API endpoints (except `/`, `/health`, `/docs`) require authentication via API key:

```bash
# Using Authorization header
curl -H "Authorization: Bearer ***" \
     -X POST https://api.ziz.ai/v1/features

# Using X-API-Key header
curl -H "X-API-Key: ***" \
     -X POST https://api.ziz.ai/v1/features
```

### Basic Flow Example

```bash
# 1. Create a feature
curl -X POST https://api.ziz.ai/v1/features \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{
    "feature_id": "chatbot-v1",
    "name": "Chatbot QA",
    "metadata": {"team": "NLP"}
  }'

# 2. Create an output
curl -X POST https://api.ziz.ai/v1/outputs \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{
    "output_id": "output-1",
    "feature_id": "chatbot-v1",
    "content": "Hello! How can I help you today?",
    "metadata": {"model": "gpt-4", "latency_ms": 1200}
  }'

# 3. Add user interaction
curl -X POST https://api.ziz.ai/v1/interactions \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_id": "interaction-1",
    "output_id": "output-1",
    "type": "feedback",
    "value": "thumbs_up",
    "metadata": {"user_id": "user-123"}
  }'

# 4. Query outputs for the feature
curl -X GET "https://api.ziz.ai/v1/features/chatbot-v1/outputs?limit=10" \
  -H "Authorization: Bearer ***"
```

### Batch Operations

```bash
# Batch create outputs
curl -X POST https://api.ziz.ai/v1/outputs/batch \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{
    "outputs": [
      {"feature_id": "f1", "content": "Response 1"},
      {"feature_id": "f1", "content": "Response 2"}
    ]
  }'
```

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Key configuration options:

- `MONGODB_URL`: MongoDB connection string
- `SECRET_KEY`: API key for authentication
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Running the API

### Development

```bash
# Install dependencies
poetry install --with dev

# Start MongoDB (if running locally)
mongod

# Run the API
poetry run uvicorn ziz.api.main:app --reload

# Or use the make command
make api
```

### Production

```bash
# Using Docker
docker build -t ziz-api --target api .
docker run -p 8000:8000 -e MONGODB_URL=mongodb://host:port ziz-api

# Or directly
poetry run uvicorn ziz.api.main:app --host 0.0.0.0 --port 8000
```

## Testing

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=ziz

# Run specific test file
poetry run pytest tests/test_api.py -v
```

## Future Provisions

The API is designed to easily support message broker integration:

1. **Storage Interface**: `StorageService` abstract class can be implemented for any message broker
2. **Decoupled Design**: Business logic is separate from persistence mechanism
3. **Event-Driven Ready**: All operations can be converted to async events
4. **Scalable Architecture**: Repository pattern supports horizontal scaling

To implement message broker support, simply:

1. Create new implementation of `StorageService` (e.g., `KafkaStorageService`)
2. Replace `storage_service` in dependency injection
3. No changes needed in routes, models, or business logic

## API Documentation

Once the API is running, visit:

- **Interactive docs**: <http://localhost:8000/docs>
- **Alternative docs**: <http://localhost:8000/redoc>
- **OpenAPI schema**: <http://localhost:8000/openapi.json>
