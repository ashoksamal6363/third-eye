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
