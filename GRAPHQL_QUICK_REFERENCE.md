# GraphQL Quick Reference

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Start services
uvicorn app.main:app --reload    # Terminal 1
python consumer/consumer.py       # Terminal 2

# 3. Open GraphiQL
# Browse to http://localhost:8000/graphql
```

## Common Queries

### Get Your Profile
```graphql
query {
  me {
    id
    username
    email
  }
}
```

### Get Your Notes
```graphql
query {
  notes {
    id
    title
    content
    tags
    createdAt
  }
}
```

### Get Your Activity Logs
```graphql
query {
  me {
    activityLogs {
      eventType
      resourceId
      timestamp
      metadata
    }
  }
}
```

### The Full Dashboard Query ⭐
```graphql
query CollabNoteDashboard {
  me {
    username
    email
    notes {
      id
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

### Get Specific User
```graphql
query {
  user(id: "1") {
    username
    email
    notes {
      title
    }
  }
}
```

### Get All Users
```graphql
query {
  users {
    id
    username
    email
  }
}
```

### Get Specific Note
```graphql
query {
  note(id: "507f1f77bcf86cd799439011") {
    title
    content
    author {
      username
    }
  }
}
```

## Common Mutations

### Create Note
```graphql
mutation {
  createNote(input: {
    title: "My Note"
    content: "This is the content"
    tags: ["important", "work"]
  }) {
    id
    title
    createdAt
  }
}
```

### Create Note (Minimal)
```graphql
mutation {
  createNote(input: {
    title: "Quick Note"
    content: "Content here"
  }) {
    id
  }
}
```

## Working with GraphiQL

### Add Authentication Token

1. Click **HTTP HEADERS** at bottom
2. Add:
```json
{
  "Authorization": "Bearer eyJhbGci..."
}
```
3. Click outside to save

### View Documentation
- Click **Docs** button (top right)
- Explore types and fields
- Click field names for details

### Format Query
- Ctrl+Shift+P (or Cmd+Shift+P on Mac) to format
- Or: Edit menu → Format

### Search Schema
- Click **Docs**
- Use search box to find types/fields

## Token Management

### Get Token from REST API

```bash
# Sign up
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user","password":"pass123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=user&password=pass123'

# Extract token from response
```

## Error Responses

### Missing Authentication
```json
{
  "errors": [{
    "message": "Authentication required. Provide Authorization: Bearer <token> header"
  }]
}
```

### Not Found
```json
{
  "errors": [{
    "message": "Note 999 not found"
  }]
}
```

### Invalid Input
```json
{
  "errors": [{
    "message": "Field validation failed"
  }]
}
```

## Field Selection

### Get Only What You Need
```graphql
# Efficient ✅
query {
  me {
    username
    email
  }
}

# Wasteful ❌
query {
  me {
    id
    username
    email
    createdAt
    notes {
      id
      title
      content
      tags
      createdAt
    }
    activityLogs {
      id
      eventType
      userId
      resourceId
      timestamp
      metadata
    }
  }
}
```

## cURL Examples

### Query via cURL
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "query": "{ me { username } }"
  }'
```

### Mutation via cURL
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "query": "mutation { createNote(input: {title: \"T\", content: \"C\"}) { id } }"
  }'
```

## Data Exploration

### See All Available Fields
1. Open GraphiQL
2. Click **Docs** (top right)
3. Click **Query** → see all queries
4. Click any type to see fields
5. Hover over field names for descriptions

### Test Complex Resolver
```graphql
query {
  notes {
    id
    title
    author {
      username
      email
      notes {
        title
      }
    }
  }
}
```

## Debugging

### Check Query Validity
GraphiQL shows errors in real-time:
- Red squiggles = syntax errors
- Hover for details
- Check Docs panel

### Monitor Request/Response
1. Open DevTools (F12)
2. Go to Network tab
3. Run query in GraphiQL
4. See request/response in Network tab

### Check Activity Logs
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

## Integration Examples

### Fetch from Frontend (JavaScript/React)
```javascript
const query = `
  query {
    me {
      username
      notes { title }
    }
  }
`;

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ query })
});

const data = await response.json();
console.log(data.data.me);
```

### Create Note from Frontend
```javascript
const mutation = `
  mutation {
    createNote(input: {
      title: "Frontend Note"
      content: "Created from React"
      tags: ["react"]
    }) {
      id
      title
    }
  }
`;

const response = await fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ mutation })
});
```

## Performance Tips

1. **Select only needed fields**
   - Smaller responses
   - Faster queries

2. **Use specific queries**
   - `notes` instead of fetching all users' notes
   - `note(id)` instead of searching all notes

3. **Limit nested depth**
   - Avoid deep nesting
   - Can cause slow queries

4. **Cache results**
   - Client-side caching
   - Save redundant queries

## Helpful Links

- **GraphiQL:** http://localhost:8000/graphql
- **REST API:** http://localhost:8000/docs
- **Docs:** [GRAPHQL_GUIDE.md](GRAPHQL_GUIDE.md)
- **Setup:** [GRAPHQL_SETUP.md](GRAPHQL_SETUP.md)

## Common Issues

| Issue | Solution |
|-------|----------|
| Token not working | Ensure format is `Bearer TOKEN` in HTTP Headers |
| Query returns null | Field might be optional, check schema |
| "Not found" error | Verify ID format (note IDs are MongoDB ObjectIds) |
| No activity logs | Ensure Kafka consumer is running |
| Slow queries | Select fewer fields, avoid deep nesting |

## Schema Quick Look

```graphql
User {
  id, username, email, createdAt
  notes → Note[]
  activityLogs → ActivityLog[]
}

Note {
  id, userId, title, content, tags, createdAt
  author → User
}

ActivityLog {
  id, eventType, userId, resourceId, timestamp, metadata
}

Query {
  me, user(id), users
  note(id), notes
}

Mutation {
  createNote(input)
}
```

---

**Tip:** Bookmark http://localhost:8000/graphql in your browser!
