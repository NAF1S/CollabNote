import os
from dotenv import load_dotenv
from fastapi import FastAPI,Depends,HTTPException,status
from fastapi import FastAPI,Depends,HTTPException,status

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import User_creadintials
from .schemas import UserCreate,UserUpdate,Userout

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME"),
    description="A collable note app",
    version="1.0.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}

@app.post("/users", response_model=Userout, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Check if email or username already exists
    existing_user = db.query(User_creadintials).filter(
        (User_creadintials.email == payload.email) | (User_creadintials.username == payload.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email or username already exists"
        )

    # Create new user
    user = User_creadintials(email=payload.email, username=payload.username)
    db.add(user)        # Add to session
    db.commit()         # Save to database
    db.refresh(user)    # Reload from database (get the ID)

    return user


@app.get("/users", response_model=list[Userout])
def list_users(db: Session = Depends(get_db)):
    return db.query(User_creadintials).order_by(User_creadintials.id.asc()).all()






