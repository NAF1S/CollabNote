from sqlalchemy import Column,Integer,String,UniqueConstraint
from .database import Base


class User_creadintials(Base):
    __tablename__ =  "User_creadintials"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    username = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
    )

    def __repr__(self):
        """String representation of User object."""
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
