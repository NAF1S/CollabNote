# GraphQL Integration Guide

## Overview

The application now exposes a full GraphQL endpoint at `/graphql` that integrates data from:
- **PostgreSQL** (users)
- **MongoDB** (notes, activity logs)
- **Kafka Events** (activity data)

## GraphQL Endpoint

**URL:** `http://localhost:8000/graphql`

**Features:**
- GraphiQL Playground at `/graphql` (browser)
- Subscriptions via WebSocket
- JWT Authentication via Bearer token

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Application

```bash
# Terminal 1: FastAPI app
uvicorn app.main:app --reload

# Terminal 2: Kafka consumer (separate)
python consumer/consumer.py
```

### 3. Access GraphiQL

Open your browser: `http://localhost:8000/graphql`

## Authentication

All queries accessing user-specific data require authentication.

### Add Token to GraphiQL

In GraphiQL, click the **HTTP HEADERS** section (bottom) and add:

```json
{
  "Authorization": "Bearer YOUR_TOKEN_HERE"
}
```

### Getting a Token

1. Sign up:
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

2. Login:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=testuser&password=password123'
```

Response contains: `"access_token": "eyJ..."`

## GraphQL Schema

### Type: User

```graphql
type User {
  id: ID!
  username: String!
  email: String!
  createdAt: DateTime!
  notes: [Note!]!                  # Resolver → MongoDB
  activityLogs: [ActivityLog!]!    # Resolver → MongoDB
}
```

### Type: Note

```graphql
type Note {
  id: ID!
  userId: Int!
  title: String!
  content: String!
  tags: [String!]!
  createdAt: DateTime!
  author: User!                    # Resolver → PostgreSQL
}
```

### Type: ActivityLog

```graphql
type ActivityLog {
  id: ID!
  eventType: String!
  userId: Int!
  resourceId: ID
  timestamp: String!               # ISO 8601
  metadata: JSON!
}
```

### Queries

#### Query: me
Returns authenticated user's full profile.

```graphql
query GetProfile {
  me {
    id
    username
    email
    createdAt
  }
}
```

#### Query: user(id: ID!)
Get a specific user by PostgreSQL ID.

```graphql
query GetUser {
  user(id: "1") {
    username
    email
    notes {
      title
    }
  }
}
```

#### Query: users
Get all users.

```graphql
query GetAllUsers {
  users {
    id
    username
    email
  }
}
```

#### Query: note(id: ID!)
Get a single note by MongoDB ObjectId.

```graphql
query GetNote {
  note(id: "507f1f77bcf86cd799439011") {
    title
    content
    tags
    author {
      username
    }
  }
}
```

#### Query: notes
Get all notes for authenticated user.

```graphql
query GetMyNotes {
  notes {
    id
    title
    content
    tags
    createdAt
  }
}
```

### Mutations

#### Mutation: createNote
Create a new note for the authenticated user.

```graphql
mutation CreateNote {
  createNote(input: {
    title: "My Note"
    content: "This is the content"
    tags: ["python", "graphql"]
  }) {
    id
    title
    createdAt
  }
}
```

## Test Scenarios

### Scenario 1: Dashboard Query (Primary Test)

This is the key test query that exercises all three data sources:

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

**Expected Result:**
- Returns authenticated user's profile
- Includes all user's notes (from MongoDB)
- Includes user's activity logs (from MongoDB)
- All data fetched in single round trip

**Steps to test:**

1. Get a valid token (signup + login)

2. Open GraphiQL at `http://localhost:8000/graphql`

3. Add token to HTTP Headers:
```json
{
  "Authorization": "Bearer YOUR_TOKEN"
}
```

4. Copy-paste the query above

5. Execute (Ctrl+Enter or click play button)

6. Verify response contains user data, notes, and activity logs

### Scenario 2: Create Note via GraphQL, View via REST

Tests that mutations sync across REST and GraphQL:

1. Execute createNote mutation:
```graphql
mutation {
  createNote(input: {
    title: "Test Note"
    content: "Created via GraphQL"
    tags: ["test"]
  }) {
    id
    title
    createdAt
  }
}
```

2. Note the returned `id`

3. Query the same note via REST:
```bash
curl -X GET http://localhost:8000/notes/RETURNED_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

4. Verify note appears with same data

### Scenario 3: Authentication Errors

Test that unauthenticated requests fail:

1. In GraphiQL, clear HTTP Headers

2. Execute: `query { notes { title } }`

3. **Expected Error:**
```json
{
  "errors": [
    {
      "message": "Authentication required. Provide Authorization: Bearer <token> header"
    }
  ]
}
```

### Scenario 4: User Resolver

Test that Note.author resolver queries PostgreSQL:

```graphql
query {
  notes {
    id
    title
    author {
      username
      email
    }
  }
}
```

**Expected:** Each note displays its creator's username and email

### Scenario 5: Activity Logs

Test that activity logs track user actions:

1. Create a note via GraphQL mutation

2. Query activity logs:
```graphql
query {
  me {
    activityLogs {
      eventType
      timestamp
      metadata
    }
  }
}
```

3. **Expected:** Latest entry is `event_type: "note_created"`

## Troubleshooting

### GraphQL endpoint returns 404

**Solution:** Ensure Strawberry packages are installed:
```bash
pip install strawberry-graphql strawberry-graphql[fastapi]
```

Then restart the server.

### "Authentication required" error on public queries

**Issue:** Queries like `users` (public) are still requiring auth.

**Solution:** Check if you're including the correct token in HTTP Headers. Some queries are public in this implementation - verify which ones need auth.

### "User not found" when accessing notes

**Issue:** Note author resolver fails.

**Solution:** Ensure note's `user_id` matches a valid PostgreSQL user. Check that note was created with correct user_id.

### MongoDB connection errors in resolvers

**Issue:** Activity logs or notes not appearing.

**Solution:** 
1. Verify MongoDB is running
2. Check `MONGODB_URL` environment variable
3. Restart the application

### Token is valid in REST but not in GraphQL

**Solution:** GraphQL tokens in GraphiQL are sent via HTTP Headers, not Authorization scheme. Format must be exactly:
```json
{
  "Authorization": "Bearer <token>"
}
```

## cURL Examples

### Get users (public query)

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ users { id username email } }"
  }'
```

### Get my profile (authenticated query)

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "{ me { username email notes { title } } }"
  }'
```

### Create note via GraphQL

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "mutation { createNote(input: { title: \"Note\", content: \"Content\", tags: [] }) { id title } }"
  }'
```

## Integration with REST API

GraphQL and REST API share the same:
- PostgreSQL database (users)
- MongoDB collections (notes, activity_logs)
- Kafka event producer
- Authentication (JWT)

**Changes to REST data are immediately visible in GraphQL and vice versa.**

### Example:

1. Create note via REST (`POST /notes`)
2. Query note via GraphQL (`query { notes { ... } }`)
3. Both see the same data

## Performance Notes

- **User.notes resolver** queries MongoDB for each user
- **User.activityLogs resolver** queries MongoDB (limited to 20 recent)
- **Note.author resolver** queries PostgreSQL for each note
- Consider DataLoader for batch optimization if queries become slow

## Type Safety

All GraphQL types are auto-generated from Python types using Strawberry decorators:

```python
@strawberry.type
class UserType:
    id: str
    username: str
    # ...
```

This ensures type consistency between Python and GraphQL schema.

## Next Steps

1. ✅ Test all queries in GraphiQL
2. ✅ Verify CollabNoteDashboard query works
3. ✅ Test authentication
4. ✅ Create notes via GraphQL mutation
5. ✅ Verify activity logs track events
6. Consider: Pagination, filtering, sorting
7. Consider: File uploads
8. Consider: Subscriptions
