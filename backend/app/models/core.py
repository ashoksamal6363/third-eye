from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

def _uuid():
    return str(uuid.uuid4())

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="org", cascade="all,delete")
    environments = relationship("Environment", back_populates="org", cascade="all,delete")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    email = Column(String, nullable=False)
    role = Column(String, nullable=False, default="admin")  # owner/admin/viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    org = relationship("Organization", back_populates="users")

class Environment(Base):
    __tablename__ = "environments"
    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    name = Column(String, nullable=False)
    region = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    org = relationship("Organization", back_populates="environments")
    cameras = relationship("Camera", back_populates="env", cascade="all,delete")

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(String, primary_key=True, default=_uuid)
    env_id = Column(String, ForeignKey("environments.id"), nullable=False)

    name = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    env = relationship("Environment", back_populates="cameras")
