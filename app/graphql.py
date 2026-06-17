from typing import Optional, List, Any, Dict
from datetime import datetime
from bson import ObjectId
import strawberry
from strawberry.types import Info
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import User_creadintials
from .mongo import get_mongodb
from .auth import decode_access_token


# ============================================================================
# GraphQL Types
# ============================================================================

@strawberry.type
class ActivityLogType:
    """Activity log entry from MongoDB."""
    id: str = strawberry.field(description="MongoDB ObjectId")
    event_type: str = strawberry.field(description="Type of event (e.g., note_created)")
    user_id: int = strawberry.field(description="User ID who triggered the event")
    resource_id: Optional[str] = strawberry.field(description="ID of affected resource")
    timestamp: str = strawberry.field(description="ISO 8601 timestamp")
    metadata: Dict[str, Any] = strawberry.field(description="Event metadata")


@strawberry.type
class NoteType:
    """Note from MongoDB."""
    id: str = strawberry.field(description="MongoDB ObjectId")
    user_id: int = strawberry.field(description="Owner's user ID")
    title: str
    content: str
    tags: List[str]
    created_at: datetime = strawberry.field(description="Note creation timestamp")
    
    @strawberry.field
    async def author(self, info: Info) -> "UserType":
        """Resolver: Get the note author from PostgreSQL."""
        db: Session = info.context.get("db")
        if not db:
            db = SessionLocal()
        
        user = db.query(User_creadintials).filter(
            User_creadintials.id == self.user_id
        ).first()
        
        if not user:
            raise Exception(f"User {self.user_id} not found")
        
        return UserType(
            id=str(user.id),
            username=user.username,
            email=user.email,
            created_at=datetime.utcnow()
        )


@strawberry.type
class UserType:
    """User from PostgreSQL."""
    id: str = strawberry.field(description="PostgreSQL user ID")
    username: str
    email: str
    created_at: datetime = strawberry.field(description="Account creation timestamp")
    
    @strawberry.field
    async def notes(self, info: Info) -> List[NoteType]:
        """Resolver: Get user's notes from MongoDB."""
        user_id = int(self.id)
        mongodb = get_mongodb()
        
        notes_docs = await mongodb.notes.find({"user_id": user_id}).to_list(None)
        
        return [
            NoteType(
                id=str(note["_id"]),
                user_id=note["user_id"],
                title=note["title"],
                content=note["content"],
                tags=note.get("tags", []),
                created_at=note["created_at"]
            )
            for note in notes_docs
        ]
    
    @strawberry.field
    async def activity_logs(self, info: Info) -> List[ActivityLogType]:
        """Resolver: Get user's activity logs from MongoDB."""
        user_id = int(self.id)
        mongodb = get_mongodb()
        
        logs = await mongodb.activity_logs.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(20).to_list(None)
        
        return [
            ActivityLogType(
                id=str(log["_id"]),
                event_type=log["event_type"],
                user_id=log["user_id"],
                resource_id=log.get("resource_id"),
                timestamp=log["timestamp"],
                metadata=log.get("metadata", {})
            )
            for log in logs
        ]


# ============================================================================
# Input Types (for mutations)
# ============================================================================

@strawberry.input
class CreateNoteInput:
    """Input for creating a new note."""
    title: str = strawberry.field(description="Note title")
    content: str = strawberry.field(description="Note content")
    tags: Optional[List[str]] = strawberry.field(default=None, description="Optional tags")


# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class Query:
    
    @strawberry.field
    async def me(self, info: Info) -> UserType:
        """
        Get authenticated user's profile.
        
        Requires: Authorization: Bearer <token> header
        """
        current_user = info.context.get("user")
        if not current_user:
            raise Exception("Authentication required. Provide Authorization: Bearer <token> header")
        
        return UserType(
            id=str(current_user.id),
            username=current_user.username,
            email=current_user.email,
            created_at=datetime.utcnow()
        )
    
    @strawberry.field
    async def user(self, info: Info, id: strawberry.ID) -> UserType:
        """Get a user by PostgreSQL ID."""
        db: Session = info.context.get("db")
        if not db:
            db = SessionLocal()
        
        user = db.query(User_creadintials).filter(
            User_creadintials.id == int(id)
        ).first()
        
        if not user:
            raise Exception(f"User {id} not found")
        
        return UserType(
            id=str(user.id),
            username=user.username,
            email=user.email,
            created_at=datetime.utcnow()
        )
    
    @strawberry.field
    async def users(self, info: Info) -> List[UserType]:
        """Get all users."""
        db: Session = info.context.get("db")
        if not db:
            db = SessionLocal()
        
        users = db.query(User_creadintials).all()
        
        return [
            UserType(
                id=str(user.id),
                username=user.username,
                email=user.email,
                created_at=datetime.utcnow()
            )
            for user in users
        ]
    
    @strawberry.field
    async def note(self, info: Info, id: strawberry.ID) -> NoteType:
        """Get a single note by MongoDB ObjectId."""
        current_user = info.context.get("user")
        if not current_user:
            raise Exception("Authentication required")
        
        try:
            object_id = ObjectId(id)
        except Exception:
            raise Exception(f"Invalid note ID format: {id}")
        
        mongodb = get_mongodb()
        note = await mongodb.notes.find_one({"_id": object_id})
        
        if not note:
            raise Exception(f"Note {id} not found")
        
        # Verify ownership
        if note["user_id"] != current_user.id:
            raise Exception("You don't have permission to view this note")
        
        return NoteType(
            id=str(note["_id"]),
            user_id=note["user_id"],
            title=note["title"],
            content=note["content"],
            tags=note.get("tags", []),
            created_at=note["created_at"]
        )
    
    @strawberry.field
    async def notes(self, info: Info) -> List[NoteType]:
        """Get all notes for the authenticated user."""
        current_user = info.context.get("user")
        if not current_user:
            raise Exception("Authentication required. Provide Authorization: Bearer <token> header")
        
        mongodb = get_mongodb()
        notes_docs = await mongodb.notes.find({"user_id": current_user.id}).to_list(None)
        
        return [
            NoteType(
                id=str(note["_id"]),
                user_id=note["user_id"],
                title=note["title"],
                content=note["content"],
                tags=note.get("tags", []),
                created_at=note["created_at"]
            )
            for note in notes_docs
        ]


# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class Mutation:
    
    @strawberry.mutation
    async def create_note(self, info: Info, input: CreateNoteInput) -> NoteType:
        """Create a new note for the authenticated user."""
        current_user = info.context.get("user")
        if not current_user:
            raise Exception("Authentication required")
        
        mongodb = get_mongodb()
        
        note_dict = {
            "user_id": current_user.id,
            "title": input.title,
            "content": input.content,
            "tags": input.tags or [],
            "created_at": datetime.utcnow()
        }
        
        result = await mongodb.notes.insert_one(note_dict)
        
        # Publish event
        from .kafka_producer import publish_event
        await publish_event(
            event_type="note_created",
            user_id=current_user.id,
            resource_id=str(result.inserted_id),
            metadata={"title": input.title, "tags": input.tags or []}
        )
        
        return NoteType(
            id=str(result.inserted_id),
            user_id=current_user.id,
            title=input.title,
            content=input.content,
            tags=input.tags or [],
            created_at=note_dict["created_at"]
        )


# ============================================================================
# Schema
# ============================================================================

schema = strawberry.Schema(query=Query, mutation=Mutation)
