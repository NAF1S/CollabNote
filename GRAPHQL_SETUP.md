# GraphQL Setup & Installation Guide

## Prerequisites

- Python 3.10+
- pip
- Running instances of:
  - PostgreSQL (for users)
  - MongoDB (for notes & activity logs)
  - Kafka (for event streaming)
  - Redis (optional, for caching)

## Installation Steps

### 1. Install Python Dependencies

```bash
cd c:\Users\DELL\Desktop\noteapp
pip install -r requirements.txt
```

**New packages added:**
- `strawberry-graphql==0.229.1` - GraphQL schema generator
- `strawberry-graphql[fastapi]==0.229.1` - FastAPI integration

### 2. Set Environment Variables

Ensure your `.env` file has:

```env
# Database
DATABASE_NAME=postgresql
SQLALCHEMY_DATABASE_URL=postgresql://user:password@localhost:5432/noteapp

# MongoDB
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=mongodb

# Kafka
KAFKA_BROKERS=localhost:9092

# App
APP_NAME=CollabNote
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Elasticsearch (optional)
ELASTICSEARCH_HOST=localhost:9200

# Redis (optional)
REDIS_URL=redis://localhost:6379
```

### 3. Start Required Services

**Option A: Using Docker Compose** (recommended)

```bash
docker-compose up -d mongodb postgresql kafka zookeeper redis
```

**Option B: Local Installations** 

Ensure these services are running:
```bash
# PostgreSQL
psql -U user -d noteapp

# MongoDB
mongod

# Kafka
kafka-server-start.sh config/server.properties

# Redis
redis-server
```

### 4. Initialize Database

```bash
# Run Alembic migrations for PostgreSQL
alembic upgrade head
```

### 5. Start the Application

**Terminal 1: FastAPI with GraphQL**
```bash
cd c:\Users\DELL\Desktop\noteapp
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Kafka Consumer** (in separate window)
```bash
cd c:\Users\DELL\Desktop\noteapp
python consumer/consumer.py
```

### 6. Verify Installation

Open your browser and navigate to:

```
http://localhost:8000/graphql
```

You should see the **GraphiQL Playground** with:
- Query editor on left
- Results pane on right
- Documentation explorer (Docs button)
- HTTP Headers section (bottom)

## File Structure

```
app/
├── graphql.py                  # GraphQL schema, types, resolvers
├── graphql_context.py          # JWT context extraction
├── main.py                     # FastAPI app + GraphQL router
├── kafka_producer.py           # Event publishing
├── mongo.py                    # MongoDB client
├── models.py                   # SQLAlchemy models
├── schemas.py                  # Pydantic schemas
├── auth.py                     # JWT utilities
└── ...

consumer/
├── consumer.py                 # Kafka consumer → MongoDB
└── mongodb.py                  # MongoDB connection manager
```

## First Test: Complete Dashboard Query

### 1. Create a Test Account

In Terminal or Postman:

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

### 2. Login to Get Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=testuser&password=password123'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Copy the `access_token` value.

### 3. Open GraphiQL

Go to: `http://localhost:8000/graphql`

### 4. Add Authentication Header

Click **HTTP HEADERS** at the bottom (if not visible, scroll down or expand):

```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

(Replace with your actual token)

### 5. Run Dashboard Query

Copy-paste this into the Query Editor:

```graphql
query CollabNoteDashboard {
  me {
    username
    email
    notes {
      title
      tags
      createdAt
    }
    activityLogs {
      eventType
      timestamp
    }
  }
}
```

Click the **Play** button (or press Ctrl+Enter).

### Expected Result

```json
{
  "data": {
    "me": {
      "username": "testuser",
      "email": "test@example.com",
      "notes": [],
      "activityLogs": [
        {
          "eventType": "user_signup",
          "timestamp": "2024-06-17T10:30:45Z"
        },
        {
          "eventType": "user_login",
          "timestamp": "2024-06-17T10:31:12Z"
        }
      ]
    }
  }
}
```

**Explanation:**
- `notes` is empty (no notes created yet)
- `activityLogs` shows signup and login events captured by Kafka consumer
- This proves all three data sources work: PostgreSQL (user), MongoDB (notes + activity_logs)

## Test: Create Note via GraphQL

In GraphiQL, run:

```graphql
mutation CreateTestNote {
  createNote(input: {
    title: "My First GraphQL Note"
    content: "Created via GraphQL endpoint"
    tags: ["graphql", "test"]
  }) {
    id
    title
    createdAt
  }
}
```

**Expected Result:**
```json
{
  "data": {
    "createNote": {
      "id": "507f1f77bcf86cd799439011",
      "title": "My First GraphQL Note",
      "createdAt": "2024-06-17T10:35:20Z"
    }
  }
}
```

## Test: Verify GraphQL ↔ REST Sync

Now verify the note appears in REST API:

```bash
curl -X GET http://localhost:8000/notes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected:**
The created note appears in the REST response with identical data.

## Test: Check Activity Logs

Run this GraphQL query:

```graphql
query {
  me {
    activityLogs(first: 5) {
      eventType
      resourceId
      metadata
      timestamp
    }
  }
}
```

**Expected:**
Latest activity includes `"eventType": "note_created"` with the note ID in `resourceId`.

## Test: Authentication Error

Try running a query WITHOUT the Authorization header:

In GraphiQL, click **HTTP HEADERS** and delete the Authorization line.

Then run:
```graphql
query {
  me {
    username
  }
}
```

**Expected Error:**
```json
{
  "errors": [
    {
      "message": "Authentication required. Provide Authorization: Bearer <token> header"
    }
  ]
}
```

## Troubleshooting

### Issue: "Import strawberry not found"

**Solution:** Strawberry is not installed yet.
```bash
pip install strawberry-graphql strawberry-graphql[fastapi]
```

Then restart the server.

### Issue: GraphQL endpoint returns 404

**Solution:**
1. Restart FastAPI: Stop and run `uvicorn app.main:app --reload` again
2. Check that `/graphql` route is registered in logs

### Issue: "PostgreSQL user not found" error

**Solution:**
- Verify PostgreSQL is running
- Check SQLALCHEMY_DATABASE_URL in `.env`
- Ensure users table exists (run alembic migrations)

### Issue: No activity logs appearing

**Solution:**
1. Check Kafka consumer is running: `python consumer/consumer.py`
2. Verify MongoDB is accessible
3. Check consumer logs for errors
4. Create a fresh action (login, create note) and query again

### Issue: "MongoDB notes.find failed"

**Solution:**
1. Verify MongoDB connection: `mongo`
2. Check MONGODB_URL in `.env`
3. Ensure `mongodb` database exists
4. Restart consumer and app

### Issue: GraphiQL UI not loading

**Solution:**
- Clear browser cache (Ctrl+Shift+Delete)
- Try incognito/private browsing
- Check browser console for errors (F12)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Application                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐                  ┌──────────────┐    │
│  │  REST API    │                  │   GraphQL    │    │
│  │  (/notes)    │────────────────→ │  (/graphql)  │    │
│  └──────────────┘                  └──────────────┘    │
│                                            │             │
│                                            ↓             │
│                              ┌──────────────────────┐   │
│                              │  JWT Context        │   │
│                              │  (Auth Header)      │   │
│                              └──────────────────────┘   │
│                                    │    │    │          │
│        ┌───────────────────────────┘    │    └────┐    │
│        ↓                                ↓         ↓    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │    │
│  │PostgreSQL│  │ MongoDB  │  │   Kafka      │   │    │
│  │ (users)  │  │ (notes)  │  │ (events)     │   │    │
│  └──────────┘  └──────────┘  └──────────────┘   │    │
│       ↑              ↑                  ↓        │    │
│       └──────────────┴──────────────────┴────────┘    │
│                                                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓
                 ┌──────────────────┐
                 │  Kafka Consumer  │
                 │ (activity logs)  │
                 └──────────────────┘
                          │
                          ↓
                 ┌──────────────────┐
                 │ MongoDB          │
                 │ activity_logs    │
                 └──────────────────┘
```

## Performance Tips

1. **Limit activity log queries:** Currently limited to 20 per user
2. **Use specific fields:** Only query fields you need
3. **Cache results:** Use Redis for frequently accessed notes
4. **Batch operations:** Create multiple notes in a single mutation flow
5. **Monitor MongoDB:** Check indexes on `activity_logs` collection

## Next Steps

- ✅ GraphQL endpoint running
- ✅ Authentication working
- ✅ All queries tested
- ✅ Mutations tested
- ✅ REST ↔ GraphQL sync verified
- 🔄 Consider: Add pagination to queries
- 🔄 Consider: Add sorting/filtering
- 🔄 Consider: GraphQL subscriptions for real-time updates

## Documentation

Full GraphQL schema documentation available at:
- **GraphiQL Docs:** http://localhost:8000/graphql (click "Docs" button)
- **Guide:** [GRAPHQL_GUIDE.md](GRAPHQL_GUIDE.md)
- **Kafka Events:** [KAFKA_ACTIVITY_LOGGING.md](KAFKA_ACTIVITY_LOGGING.md)

## Support

For issues:
1. Check logs in terminal windows
2. Check `.env` configuration
3. Verify all services are running
4. Consult troubleshooting section above
5. Check browser console for client-side errors (F12)
