from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.datastructures import Headers

from .database import SessionLocal
from .models import User_creadintials
from .auth import decode_access_token


async def get_graphql_context(request: Request) -> Dict[str, Any]:
    """
    Build GraphQL context from request.
    
    Extracts JWT from Authorization header, validates it, and includes:
    - authenticated user
    - database session
    """
    context: Dict[str, Any] = {}
    db = SessionLocal()
    context["db"] = db
    
    # Try to extract and validate JWT from Authorization header
    auth_header = request.headers.get("Authorization", "")
    
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        email = decode_access_token(token)
        
        if email:
            user = db.query(User_creadintials).filter(
                User_creadintials.email == email
            ).first()
            
            if user:
                context["user"] = user
    
    return context
