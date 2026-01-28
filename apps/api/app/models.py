from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .db import Base

def _uuid(): return str(uuid.uuid4())

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    email = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin")  # owner/admin/viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Environment(Base):
    __tablename__ = "environments"
    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    region = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(String, primary_key=True, default=_uuid)
    env_id = Column(String, ForeignKey("environments.id"), nullable=False)
    name = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TenantConfig(Base):
    __tablename__ = "tenant_config"
    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, unique=True)

    llama1_url = Column(String, nullable=False)
    llama1_key = Column(String, nullable=False)
    llama2_url = Column(String, nullable=False)
    llama2_key = Column(String, nullable=False)

    decision_policy = Column(String, default="majority_vote")  # majority_vote | avg_score
    sms_numbers = Column(Text, default="")  # comma separated
    whatsapp_numbers = Column(Text, default="")  # comma separated

class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"
    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    blob_url = Column(Text, nullable=True)

    llm1_flag = Column(Boolean, default=False)
    llm1_reason = Column(Text, default="")
    llm1_score = Column(String, default="")

    llm2_flag = Column(Boolean, default=False)
    llm2_reason = Column(Text, default="")
    llm2_score = Column(String, default="")

    final_flag = Column(Boolean, default=False)
    final_reason = Column(Text, default="")

class HumanLabel(Base):
    __tablename__ = "human_labels"
    id = Column(String, primary_key=True, default=_uuid)
    event_id = Column(String, ForeignKey("anomaly_events.id"), nullable=False)
    labeled_by = Column(String, default="admin")
    is_anomaly = Column(Boolean, nullable=False)
    justification = Column(Text, default="")
    labeled_at = Column(DateTime, default=datetime.utcnow)
