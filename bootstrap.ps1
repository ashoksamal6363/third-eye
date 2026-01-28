# Third Eye Monorepo Bootstrap
$ErrorActionPreference = "Stop"

function WriteFile($path, $content) {
  $dir = Split-Path $path
  if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $content | Set-Content -Encoding utf8 $path
  Write-Host "Wrote $path"
}

# Root files
WriteFile ".gitignore" @"
.env
.env.*
**/.env
**/.env.*
node_modules
.next
dist
__pycache__/
*.pyc
.venv/
venv/
*.log
"@

WriteFile "README.md" @"
# Third Eye (Multi-tenant Anomaly Detection)

Monorepo:
- apps/api    FastAPI + Postgres + JWT + Blob + Twilio
- apps/worker Camera polling + LLM1/LLM2 + anomaly pipeline
- apps/web    Next.js admin console (envs/cameras/users/anomalies)

Local run: docker compose up
"@

WriteFile "docker-compose.yml" @"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: third_eye
      POSTGRES_PASSWORD: third_eye_password
      POSTGRES_DB: third_eye
    ports: ["5432:5432"]
    volumes: ["dbdata:/var/lib/postgresql/data"]

  api:
    build: ./apps/api
    environment:
      DATABASE_URL: postgresql+psycopg2://third_eye:third_eye_password@db:5432/third_eye
      JWT_SECRET: dev_secret_change_me
      API_BASE_URL: http://localhost:8001
      AZURE_BLOB_ACCOUNT_URL: ""
      AZURE_BLOB_CONTAINER: "camera-frames"
      AZURE_BLOB_SAS: ""
      TWILIO_ACCOUNT_SID: ""
      TWILIO_AUTH_TOKEN: ""
      TWILIO_FROM_NUMBER: ""
    ports: ["8001:8001"]
    depends_on: [db]

  worker:
    build: ./apps/worker
    environment:
      API_BASE_URL: http://api:8001
      WORKER_POLL_SECONDS: "10"
    depends_on: [api]

  web:
    build: ./apps/web
    environment:
      NEXT_PUBLIC_API_BASE: http://localhost:8001
    ports: ["3000:3000"]
    depends_on: [api]

volumes:
  dbdata:
"@

# API (FastAPI)
WriteFile "apps/api/Dockerfile" @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8001
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8001"]
"@

WriteFile "apps/api/requirements.txt" @"
fastapi==0.115.6
uvicorn[standard]==0.30.6
python-dotenv==1.0.1
SQLAlchemy==2.0.36
psycopg2-binary==2.9.10
pydantic==2.10.3
PyJWT==2.10.1
requests==2.32.3
azure-storage-blob==12.23.1
twilio==9.4.0
"@

WriteFile "apps/api/app/db.py" @"
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL missing")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"@

WriteFile "apps/api/app/models.py" @"
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
"@

WriteFile "apps/api/app/security.py" @"
import os, time, jwt, hashlib

JWT_SECRET = os.getenv("JWT_SECRET", "change_me")

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def sign_token(user_id: str, org_id: str, role: str) -> str:
    payload = {"sub": user_id, "org": org_id, "role": role, "iat": int(time.time())}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
"@

WriteFile "apps/api/app/main.py" @"
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models import Organization, User, Environment, Camera, TenantConfig, AnomalyEvent, HumanLabel
from .security import hash_pw, sign_token, verify_token

app = FastAPI(title="Third Eye API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

def auth(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        return verify_token(token)
    except Exception:
        raise HTTPException(401, "invalid token")

@app.get("/health")
def health():
    return {"status":"ok"}

# --- bootstrap: create org + owner user ---
@app.post("/bootstrap")
def bootstrap(org_name: str, owner_email: str, owner_password: str, db: Session = Depends(get_db)):
    org = Organization(name=org_name)
    db.add(org); db.commit(); db.refresh(org)

    u = User(org_id=org.id, email=owner_email, password_hash=hash_pw(owner_password), role="owner")
    db.add(u); db.commit(); db.refresh(u)

    return {"org_id": org.id, "owner_user_id": u.id}

@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == email).first()
    if not u or u.password_hash != hash_pw(password) or not u.is_active:
        raise HTTPException(401, "bad credentials")
    return {"token": sign_token(u.id, u.org_id, u.role), "org_id": u.org_id, "role": u.role}

# --- tenant resources ---
@app.get("/envs")
def list_envs(org_id: str, claims=Depends(auth), db: Session = Depends(get_db)):
    if claims["org"] != org_id: raise HTTPException(403, "wrong org")
    return db.query(Environment).filter(Environment.org_id == org_id).all()

@app.post("/envs")
def create_env(org_id: str, name: str, region: str = "", claims=Depends(auth), db: Session = Depends(get_db)):
    if claims["org"] != org_id: raise HTTPException(403, "wrong org")
    env = Environment(org_id=org_id, name=name, region=region or None)
    db.add(env); db.commit(); db.refresh(env)
    return env

@app.get("/cameras")
def list_cameras(env_id: str, claims=Depends(auth), db: Session = Depends(get_db)):
    env = db.get(Environment, env_id)
    if not env or env.org_id != claims["org"]: raise HTTPException(404, "env not found")
    return db.query(Camera).filter(Camera.env_id == env_id).all()

@app.post("/cameras")
def create_camera(env_id: str, name: str, rtsp_url: str, claims=Depends(auth), db: Session = Depends(get_db)):
    env = db.get(Environment, env_id)
    if not env or env.org_id != claims["org"]: raise HTTPException(404, "env not found")
    cam = Camera(env_id=env_id, name=name, rtsp_url=rtsp_url, enabled=True)
    db.add(cam); db.commit(); db.refresh(cam)
    return cam

@app.get("/events")
def list_events(org_id: str, claims=Depends(auth), db: Session = Depends(get_db)):
    if claims["org"] != org_id: raise HTTPException(403, "wrong org")
    return db.query(AnomalyEvent).filter(AnomalyEvent.org_id == org_id).order_by(AnomalyEvent.created_at.desc()).limit(200).all()

@app.post("/events/{event_id}/label")
def label_event(event_id: str, is_anomaly: bool, justification: str = "", claims=Depends(auth), db: Session = Depends(get_db)):
    ev = db.get(AnomalyEvent, event_id)
    if not ev or ev.org_id != claims["org"]: raise HTTPException(404, "event not found")
    row = HumanLabel(event_id=event_id, labeled_by=claims["sub"], is_anomaly=is_anomaly, justification=justification)
    db.add(row); db.commit()
    return {"ok": True}
"@

# Worker
WriteFile "apps/worker/Dockerfile" @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libgl1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY worker.py .
CMD ["python","worker.py"]
"@

WriteFile "apps/worker/requirements.txt" @"
requests==2.32.3
opencv-python==4.13.0.90
"@

WriteFile "apps/worker/worker.py" @"
import os, time, requests
API = os.getenv("API_BASE_URL", "http://localhost:8001")
POLL = int(os.getenv("WORKER_POLL_SECONDS","10"))

print(f"[worker] API={API} POLL={POLL}")

# Placeholder: in production, worker authenticates as org service account and pulls enabled cameras per org/env.
# For now, worker is a scaffold—your existing anomaly detector logic is plugged here next.

while True:
    try:
        # health check just to keep container alive
        r = requests.get(f"{API}/health", timeout=5)
        print("[worker] health:", r.status_code)
    except Exception as e:
        print("[worker] err:", e)
    time.sleep(POLL)
"@

# Web (Next.js minimal scaffold; we will match screenshots after you answer auth + hosting)
WriteFile "apps/web/Dockerfile" @"
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm","run","dev","--","-p","3000","-H","0.0.0.0"]
"@

WriteFile "apps/web/package.json" @"
{
  "name": "third-eye-web",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start -p 3000"
  },
  "dependencies": {
    "next": "14.2.5",
    "react": "18.3.1",
    "react-dom": "18.3.1"
  }
}
"@

WriteFile "apps/web/next.config.js" @"
/** @type {import('next').NextConfig} */
const nextConfig = {};
module.exports = nextConfig;
"@

WriteFile "apps/web/src/app/layout.tsx" @"
export const metadata = { title: 'Third Eye' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='en'>
      <body style={{ fontFamily: 'system-ui', margin: 0 }}>{children}</body>
    </html>
  );
}
"@

WriteFile "apps/web/src/app/page.tsx" @"
export default function Page() {
  return (
    <main style={{ padding: 24 }}>
      <h1>Third Eye</h1>
      <p>Web app scaffold created. Next step: paste your exact UI layout + pages.</p>
    </main>
  );
}
"@

Write-Host "`nBootstrap complete."
