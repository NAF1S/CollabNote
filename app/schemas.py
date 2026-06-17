from pydantic import BaseModel,EmailStr,Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email:EmailStr
    username:str = Field(
        min_length=3,
        max_length=50
    )
    password : str = Field(min_length=6,description="Minimum 6 digits")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "alice@example.com",
                "username": "alice",
                "password": "securepassword123"
            }
        }

class UserUpdate(BaseModel):
    email:EmailStr | None = None
    username:str | None = Field(
        default=None,
        min_length=3,
        max_length=50
    )
class Userout(BaseModel):
    id:int
    email:EmailStr
    username : str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "alice@example.com",
                "username": "alice"
            }
        }


class Token(BaseModel):
    access_token : str
    token_type : str = "bearer"

    class config:
        json_schema_extra = {
            "example" : {
                "access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type":"bearer"
            }
        }

class TokenData(BaseModel):
    email : Optional[str] = None



class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Note title")
    content: str = Field(..., min_length=1, description="Note content")
    tags: Optional[list[str]] = Field(default=[], description="Optional tags for categorization")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Learn FastAPI",
                "content": "FastAPI is a modern web framework for building APIs",
                "tags": ["python", "fastapi", "tutorial"]
            }
        }

class NoteResponse(BaseModel):
    id: str = Field(..., description="Unique identifier (MongoDB ObjectId)")
    title: str
    content: str
    tags: list[str]
    created_at: datetime = Field(..., description="Timestamp when note was created")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "title": "Learn FastAPI",
                "content": "FastAPI is a modern web framework",
                "tags": ["python", "fastapi"],
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[list[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Title",
                "tags": ["python", "fastapi", "mongodb"]
            }
        }
class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    tags: list[str]
    score: float
    highlight: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "title": "FastAPI Tutorial",
                "content": "FastAPI is a modern web framework...",
                "tags": ["fastapi", "python"],
                "score": 8.5,
                "highlight": {
                    "title": ["<em>FastAPI</em> Tutorial"]
                }
            }
        }


class ActivityLog(BaseModel):
    id: str = Field(..., alias="_id", description="MongoDB ObjectId")
    event_type: str = Field(..., description="Type of event (user_signup, note_created, etc.)")
    user_id: int = Field(..., description="ID of the user who triggered the event")
    resource_id: Optional[str] = Field(None, description="ID of affected resource (e.g., note ID)")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the event")
    metadata: dict = Field(default_factory=dict, description="Additional event metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "event_type": "note_created",
                "user_id": 1,
                "resource_id": "507f1f77bcf86cd799439012",
                "timestamp": "2024-06-17T10:30:45Z",
                "metadata": {"title": "My Note", "tags": ["python"]}
            }
        }