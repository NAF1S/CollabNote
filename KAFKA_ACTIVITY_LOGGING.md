# Kafka Event Publishing & Activity Logging System

This document describes the Kafka event publishing system integrated into the FastAPI application and the standalone consumer that logs events to MongoDB.

## Overview

The system publishes events to a Kafka topic (`collabnote_events`) whenever users perform key actions, and a standalone consumer reads these events and stores them in MongoDB's `activity_logs` collection.

### Architecture

```
FastAPI App (Event Producer)
    ↓ (publish events to Kafka)
Kafka Topic: collabnote_events
    ↓ (consume events from Kafka)
Standalone Consumer
    ↓ (write logs to MongoDB)
MongoDB: activity_logs collection
    ↓ (retrieve via API)
GET /activity endpoint
```

## Event Publishing

### Supported Events

The following events are automatically published when users perform actions:

| Event Type | Trigger | Resource ID | Metadata |
|------------|---------|-------------|----------|
| `user_signup` | User registration | N/A | `email`, `username` |
| `user_login` | User authentication | N/A | `username` |
| `note_created` | New note created | Note ID | `title`, `tags` |
| `note_updated` | Note modified | Note ID | `updated_fields` |
| `note_deleted` | Note removed | Note ID | N/A |
| `note_searched` | Search performed | N/A | `query`, `results_count` |

### Event Payload Structure

Each event contains:

```json
{
  "event_type": "string",                    // Type of event
  "user_id": "integer",                      // ID of performing user
  "resource_id": "string (optional)",        // ID of affected resource
  "timestamp": "ISO 8601 string",            // UTC timestamp with Z suffix
  "metadata": {                              // Additional event context
    "key1": "value1",
    "key2": "value2"
  }
}
```

### Example Event (Note Created)

```json
{
  "event_type": "note_created",
  "user_id": 1,
  "resource_id": "507f1f77bcf86cd799439011",
  "timestamp": "2024-06-17T10:30:45Z",
  "metadata": {
    "title": "My First Note",
    "tags": ["python", "fastapi"]
  }
}
```

## Configuration

### Environment Variables

Add the following to your `.env` file:

```env
# Kafka Configuration
KAFKA_BROKERS=localhost:9092          # Comma-separated broker addresses
                                      # Example: broker1:9092,broker2:9092

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=mongodb
```

### Kafka Setup

If using Docker Compose, add Kafka service:

```yaml
kafka:
  image: confluentinc/cp-kafka:latest
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
    KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
  ports:
    - "9092:9092"
  depends_on:
    - zookeeper

zookeeper:
  image: confluentinc/cp-zookeeper:latest
  environment:
    ZOOKEEPER_CLIENT_PORT: 2181
  ports:
    - "2181:2181"
```

## Running the Consumer

### Standalone Execution

Start the Kafka consumer as a separate service:

```bash
cd consumer/
python consumer.py
```

The consumer will:
1. Connect to MongoDB and Kafka
2. Listen for events on the `collabnote_events` topic
3. Write each event to MongoDB's `activity_logs` collection
4. Continue running indefinitely

### With Docker

Create a `Dockerfile` for the consumer:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY consumer/ .

CMD ["python", "consumer.py"]
```

Run with Docker Compose:

```yaml
consumer:
  build:
    context: .
    dockerfile: Dockerfile.consumer
  environment:
    KAFKA_BROKERS: kafka:29092
    MONGODB_URL: mongodb://mongodb:27017
    DATABASE_NAME: mongodb
  depends_on:
    - kafka
    - mongodb
```

## Activity Logs API

### Retrieve Activity Logs

**Endpoint:** `GET /activity`

**Authentication:** Required (Bearer token)

**Response:** Array of activity log entries (max 20, sorted by timestamp descending)

#### Request Example

```bash
curl -X GET http://localhost:8000/activity \
  -H "Authorization: Bearer <your_access_token>"
```

#### Response Example

```json
[
  {
    "id": "507f1f77bcf86cd799439013",
    "event_type": "note_created",
    "user_id": 1,
    "resource_id": "507f1f77bcf86cd799439011",
    "timestamp": "2024-06-17T10:35:20Z",
    "metadata": {
      "title": "My Note",
      "tags": ["python"]
    }
  },
  {
    "id": "507f1f77bcf86cd799439012",
    "event_type": "user_login",
    "user_id": 1,
    "resource_id": null,
    "timestamp": "2024-06-17T10:30:45Z",
    "metadata": {
      "username": "alice"
    }
  }
]
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | MongoDB ObjectId of the log entry |
| `event_type` | string | Type of event that occurred |
| `user_id` | integer | ID of user who triggered event |
| `resource_id` | string (nullable) | ID of affected resource (null if N/A) |
| `timestamp` | string | ISO 8601 timestamp in UTC |
| `metadata` | object | Event-specific metadata |

#### Error Responses

**401 Unauthorized** - Missing or invalid authentication token:
```json
{
  "detail": "Could not validate credentials"
}
```

**500 Internal Server Error** - MongoDB connectivity issue:
```json
{
  "detail": "Failed to retrieve activity logs"
}
```

## Kafka Producer Module

The Kafka producer is initialized automatically on application startup and closed on shutdown.

### Using the Producer

To manually publish an event (if needed):

```python
from app.kafka_producer import publish_event

# Publish event
await publish_event(
    event_type="custom_event",
    user_id=1,
    resource_id="some_id",
    metadata={"custom_field": "value"}
)
```

### Producer Configuration

Located in `app/kafka_producer.py`:

- **Bootstrap Servers:** Configurable via `KAFKA_BROKERS` environment variable
- **Topic:** `collabnote_events` (hardcoded)
- **Serializer:** JSON with UTF-8 encoding
- **Mode:** Fire-and-forget (non-blocking)

## MongoDB Collections

### activity_logs Collection

Documents are automatically indexed with:
- Compound index on `(user_id, timestamp)` for efficient queries

**Document Structure:**

```javascript
{
  "_id": ObjectId("..."),
  "event_type": "string",
  "user_id": integer,
  "resource_id": "string or null",
  "timestamp": "ISO 8601 string",
  "metadata": { /* dynamic fields */ }
}
```

### Example MongoDB Query

Retrieve last 10 activities for user 1:

```javascript
db.activity_logs.find({ user_id: 1 })
  .sort({ timestamp: -1 })
  .limit(10)
```

## Troubleshooting

### Consumer not receiving events

1. **Check Kafka connectivity:**
   ```bash
   # Verify consumer group
   kafka-consumer-groups --bootstrap-server localhost:9092 --list
   ```

2. **Verify topic exists:**
   ```bash
   kafka-topics --bootstrap-server localhost:9092 --list | grep collabnote_events
   ```

3. **Check consumer logs** for error messages

### Events not in MongoDB

1. Ensure MongoDB connection is working
2. Check database name matches `DATABASE_NAME` environment variable
3. Verify collection `activity_logs` exists or will be auto-created

### Application won't start

1. Ensure `KAFKA_BROKERS` is accessible
2. Check all required environment variables are set
3. Review application logs for connection errors

## Testing the System

### Manual Test Flow

1. **Start the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Start the consumer:**
   ```bash
   python consumer/consumer.py
   ```

3. **Create a test account:**
   ```bash
   curl -X POST http://localhost:8000/auth/signup \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "username": "testuser",
       "password": "password123"
     }'
   ```

4. **Login:**
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d 'username=testuser&password=password123'
   ```

5. **Create a note (publishes `note_created` event):**
   ```bash
   curl -X POST http://localhost:8000/notes \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Test Note",
       "content": "This is a test",
       "tags": ["test"]
     }'
   ```

6. **Check activity logs:**
   ```bash
   curl -X GET http://localhost:8000/activity \
     -H "Authorization: Bearer <token>"
   ```

## Performance Notes

- Events are published asynchronously (fire-and-forget)
- Consumer processes events sequentially
- Activity logs are limited to 20 most recent per user
- MongoDB query uses indexed timestamp for efficiency
- Consumer supports horizontal scaling via Kafka consumer groups

## Future Enhancements

- Activity log pagination (offset/limit parameters)
- Event filtering by type
- Date range filtering
- Bulk event replay
- Analytics dashboard
- Event retention policies
- Real-time WebSocket updates
