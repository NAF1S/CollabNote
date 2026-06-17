import os
from dotenv import load_dotenv
from fastapi import FastAPI,Depends,HTTPException,status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials,OAuth2PasswordRequestForm

from datetime import timedelta,datetime

from bson import ObjectId

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import User_creadintials
from .schemas import UserCreate,UserUpdate,Userout,Token,TokenData,NoteCreate,NoteResponse,NoteUpdate,SearchResult,ActivityLog
from .mongo import connect_to_mongodb,close_mongodb_connection,get_mongodb
from .elasticsearch import connect_to_elasticsearch,close_elasticsearch_connection,get_elasticsearch,ELASTICSEARCH_INDEX
from .redis_client import connect_to_redis,close_redis_connection,cache_get,cache_set,cache_delete,CACHE_TTL
from .kafka_producer import init_kafka_producer, close_kafka_producer, publish_event
from .graphql import schema
from .graphql_context import get_graphql_context

from strawberry.asgi import GraphQL

from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME"),
    description="A collable note app",
    version="1.0.0"
)

security = HTTPBearer()

# ============================================================================
# GraphQL Setup
# ============================================================================

graphql_app = GraphQL(
    schema,
    context_getter=get_graphql_context,
    debug=True
)

app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongodb()
    await connect_to_redis()
    await init_kafka_producer()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongodb_connection()
    await close_redis_connection()
    await close_kafka_producer()

def note_helper(note) -> dict:
    """
    Convert MongoDB document to API response format.

    Converts ObjectId to string and structures data according to NoteResponse schema.
    """
    return {
        "id": str(note["_id"]),
        "title": note["title"],
        "content": note["content"],
        "tags": note.get("tags", []),
        "created_at": note["created_at"]
    }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User_creadintials:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract token from credentials
    token = credentials.credentials

    # Decode token
    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    # Get user from database
    user = db.query(User_creadintials).filter(User_creadintials.email == email).first()
    if user is None:
        raise credentials_exception

    return user

@app.post("/auth/signup", response_model=Userout, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User_creadintials).filter(
        (User_creadintials.email == user_data.email) | (User_creadintials.username == user_data.username)
    ).first()

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user
    new_user = User_creadintials(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Publish user_signup event (fire-and-forget)
    await publish_event(
        event_type="user_signup",
        user_id=new_user.id,
        metadata={"email": new_user.email, "username": new_user.username}
    )

    return new_user
@app.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Find user by username
    user = db.query(User_creadintials).filter(User_creadintials.username == form_data.username).first()

    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    # Publish user_login event (fire-and-forget)
    await publish_event(
        event_type="user_login",
        user_id=user.id,
        metadata={"username": user.username}
    )

    return {"access_token": access_token, "token_type": "bearer"}

    

@app.get("/profile", response_model=Userout)
def get_profile(current_user: User_creadintials = Depends(get_current_user)):
    return current_user


# mondo db stuff

@app.get("/")
async def root():
    return {
        "message": "Welcome to FastAPI Lab 3 - MongoDB Integration",
        "endpoints": {
            "create_note": "POST /notes",
            "get_all_notes": "GET /notes",
            "get_note": "GET /notes/{id}",
            "update_note": "PUT /notes/{id}",
            "delete_note": "DELETE /notes/{id}"
        }
    }

@app.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(note: NoteCreate, current_user = Depends(get_current_user)):
    mongodb = get_mongodb()
    es = get_elasticsearch()
    note_dict = note.model_dump()
    note_dict["user_id"] = current_user.id
    note_dict["created_at"] = datetime.utcnow()
    result = await mongodb.notes.insert_one(note_dict)
    
    # Retrieve the created note
    created_note = await mongodb.notes.find_one({"_id": result.inserted_id})

    await es.index(
        index = ELASTICSEARCH_INDEX,
        id = str(result.inserted_id),
        document={
            "title": note.title,
            "content": note.content,
            "tags": note.tags,
            "created_at": note_dict["created_at"].isoformat()
        }
    )

    # Publish note_created event (fire-and-forget)
    await publish_event(
        event_type="note_created",
        user_id=current_user.id,
        resource_id=str(result.inserted_id),
        metadata={"title": note.title, "tags": note.tags}
    )

    return note_helper(created_note)



@app.get("/notes",response_model=list[NoteResponse])
async def get_notes(current_user = Depends(get_current_user)):
    db = get_mongodb()
    id = current_user.id
    notes = await db.notes.find({"user_id" : current_user.id}).to_list(None)
    return [note_helper(note) for note in notes]


@app.get("/notes/{id}", response_model=NoteResponse)
async def get_note(id: str, current_user=Depends(get_current_user)):
    """
    Get a specific note by ID with Redis caching.
    
    - **id**: The note ID (MongoDB ObjectId)
    - **current_user**: Authenticated user (required)
    
    Returns the note with Cache header indicating HIT or MISS.
    Raises 400 if note ID format is invalid.
    Raises 403 if user is not the note owner.
    Raises 404 if note not found.
    """
    from fastapi.responses import JSONResponse
    
    try:
        object_id = ObjectId(id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )
    
    cache_key = f"note:{id}"
    
    # Check Redis cache first
    cached_note = await cache_get(cache_key)
    if cached_note:
        # Verify ownership even from cache
        if cached_note.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this note"
            )
        return JSONResponse(
            content=cached_note,
            headers={"Cache": "HIT"}
        )
    
    # Cache miss - query MongoDB
    db = get_mongodb()
    note = await db.notes.find_one({"_id": object_id, "user_id": current_user.id})
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you don't have permission to view it"
        )
    
    note_data = note_helper(note)
    note_data["user_id"] = current_user.id
    
    # Store in Redis cache with TTL
    await cache_set(cache_key, note_data, ttl=CACHE_TTL)
    
    return JSONResponse(
        content=note_data,
        headers={"Cache": "MISS"}
    )

@app.put("/notes/{id}",response_model=NoteResponse)
async def up_note(id:str,note_update:NoteUpdate,current_user=Depends(get_current_user)):
    """
    Update a note. Only the note owner may update.
    
    - **id**: The note ID (MongoDB ObjectId)
    - **note_update**: Fields to update (title, content, tags)
    - **current_user**: Authenticated user (required)
    
    Updates MongoDB, re-indexes in Elasticsearch, and invalidates Redis cache.
    """
    try:
        object_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid note ID format")
    db = get_mongodb()
    es = get_elasticsearch()
    
    note = await db.notes.find_one({"_id":object_id,"user_id":current_user.id})
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you don't have permission to update it")
    update_data = note_update.model_dump(exclude_unset=True)
    result = await db.notes.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )
    updated_note = await db.notes.find_one({"_id": object_id})
    
    # Re-index in Elasticsearch
    try:
        await es.index(
            index=ELASTICSEARCH_INDEX,
            id=id,
            document={
                "title": updated_note.get("title", ""),
                "content": updated_note.get("content", ""),
                "tags": updated_note.get("tags", []),
                "created_at": updated_note.get("created_at", "").isoformat() if updated_note.get("created_at") else ""
            }
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Warning: Failed to re-index note {id} in Elasticsearch: {str(e)}")
    
    # Invalidate cache for this note
    cache_key = f"note:{id}"
    await cache_delete(cache_key)

    # Publish note_updated event (fire-and-forget)
    await publish_event(
        event_type="note_updated",
        user_id=current_user.id,
        resource_id=id,
        metadata={"updated_fields": list(update_data.keys())}
    )
    
    return note_helper(updated_note)

@app.delete("/notes/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(id: str, current_user=Depends(get_current_user)):
    """
    Delete a note from MongoDB. Only the note owner may delete.
    
    - **id**: The note ID (MongoDB ObjectId)
    - **current_user**: Authenticated user (required)
    
    Returns 204 No Content on success.
    Raises 400 if note ID format is invalid.
    Raises 403 if user is not the note owner.
    Raises 404 if note not found.
    """
    try:
        object_id = ObjectId(id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )
    
    db = get_mongodb()
    es = get_elasticsearch()
    
    # Check if note exists and belongs to the current user
    note = await db.notes.find_one({"_id": object_id, "user_id": current_user.id})
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you don't have permission to delete it"
        )
    
    # Delete from MongoDB
    await db.notes.delete_one({"_id": object_id})
    
    # Delete from Elasticsearch
    try:
        await es.delete(index=ELASTICSEARCH_INDEX, id=id)
    except Exception:
        # If note doesn't exist in Elasticsearch, continue anyway
        pass
    
    # Invalidate cache
    cache_key = f"note:{id}"
    await cache_delete(cache_key)

    # Publish note_deleted event (fire-and-forget)
    await publish_event(
        event_type="note_deleted",
        user_id=current_user.id,
        resource_id=id
    )
    
    return None

@app.get("users/{user_id}/notes",response_model=list[NoteResponse])
async def get_all_notes(user_id:int,current_user=Depends(get_current_user),db: Session = Depends(get_db)):
    user  = db.query(User_creadintials).filter(User_creadintials.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You don't have permission to view this user's notes")
    mondb = get_mongodb()
    notes = await mondb.notes.find({"user_id":user_id}).to_list(None)
    return [note_helper(note) for note in notes]


@app.get("/search", response_model=list[SearchResult])
async def search_notes(
    q: str = None,
    current_user=Depends(get_current_user)
):
    """
    Search notes using Elasticsearch with multi_match query.
    
    - **q**: Search term (required)
    - **current_user**: Authenticated user (required)
    
    Features:
    - Title field boosted 3x for higher relevance
    - Content field for full text search
    - Fuzziness: AUTO for typo tolerance
    - Results sorted by relevance score
    - Highlighted snippets showing matched text
    """
    if not q or q.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query 'q' is required and cannot be empty"
        )
    
    es = get_elasticsearch()
    
    # Build multi_match query with title boosted 3x and content, with AUTO fuzziness
    query = {
        "multi_match": {
            "query": q,
            "fields": [
                "title^3",  # Title boosted 3x
                "content"
            ],
            "fuzziness": "AUTO",
            "operator": "or"
        }
    }
    
    # Execute search with highlighting
    try:
        response = await es.search(
            index=ELASTICSEARCH_INDEX,
            body={
                "query": query,
                "highlight": {
                    "fields": {
                        "title": {},
                        "content": {
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        }
                    },
                    "pre_tags": ["<em>"],
                    "post_tags": ["</em>"]
                },
                "size": 100  # Return up to 100 results
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
    
    # Process results and filter by current user
    results = []
    mongodb = get_mongodb()
    
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        
        # Verify user ownership - only return notes belonging to current user
        note_doc = await mongodb.notes.find_one({"_id": ObjectId(hit["_id"])})
        if not note_doc or note_doc.get("user_id") != current_user.id:
            continue
        
        # Build highlight dictionary
        highlight = hit.get("highlight", {})
        
        result = SearchResult(
            id=hit["_id"],
            title=source.get("title", ""),
            content=source.get("content", ""),
            tags=source.get("tags", []),
            score=hit["_score"],
            highlight=highlight if highlight else None
        )
        results.append(result)
    
    # Publish note_searched event (fire-and-forget)
    await publish_event(
        event_type="note_searched",
        user_id=current_user.id,
        metadata={"query": q, "results_count": len(results)}
    )

    # Results are already sorted by relevance score (Elasticsearch default)
    return results


@app.get("/activity", response_model=list[ActivityLog])
async def get_activity(current_user: User_creadintials = Depends(get_current_user)):
    """
    Get the last 20 activity log entries for the authenticated user.
    
    Returns activity logs sorted by timestamp descending (most recent first).
    Each entry shows event_type, resource_id, timestamp, and metadata.
    
    - **current_user**: Authenticated user (required)
    
    Protected endpoint - requires valid bearer token.
    """
    mongodb = get_mongodb()
    
    try:
        # Query activity logs for the current user, sorted by timestamp descending
        # Limit to 20 most recent entries
        activity_logs = await mongodb.activity_logs.find(
            {"user_id": current_user.id}
        ).sort("timestamp", -1).limit(20).to_list(None)
        
        # Transform MongoDB documents to ActivityLog response format
        results = []
        for log in activity_logs:
            activity = ActivityLog(
                _id=str(log["_id"]),
                event_type=log["event_type"],
                user_id=log["user_id"],
                resource_id=log.get("resource_id"),
                timestamp=log["timestamp"],
                metadata=log.get("metadata", {})
            )
            results.append(activity)
        
        return results
    
    except Exception as e:
        print(f"Error retrieving activity logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity logs"
        )