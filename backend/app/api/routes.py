from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.core import Organization, Environment, Camera
from app.api.schemas import OrgCreate, OrgOut, EnvCreate, EnvOut, CameraCreate, CameraOut

router = APIRouter()

@router.post('/orgs', response_model=OrgOut)
def create_org(payload: OrgCreate, db: Session = Depends(get_db)):
    org = Organization(name=payload.name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

@router.get('/orgs', response_model=list[OrgOut])
def list_orgs(db: Session = Depends(get_db)):
    return db.query(Organization).all()

@router.post('/envs', response_model=EnvOut)
def create_env(payload: EnvCreate, db: Session = Depends(get_db)):
    org = db.get(Organization, payload.org_id)
    if not org:
        raise HTTPException(404, 'org not found')
    env = Environment(org_id=payload.org_id, name=payload.name, region=payload.region)
    db.add(env)
    db.commit()
    db.refresh(env)
    return env

@router.get('/envs', response_model=list[EnvOut])
def list_envs(org_id: str, db: Session = Depends(get_db)):
    return db.query(Environment).filter(Environment.org_id == org_id).all()

@router.post('/cameras', response_model=CameraOut)
def create_camera(payload: CameraCreate, db: Session = Depends(get_db)):
    env = db.get(Environment, payload.env_id)
    if not env:
        raise HTTPException(404, 'env not found')
    cam = Camera(env_id=payload.env_id, name=payload.name, rtsp_url=payload.rtsp_url, enabled=payload.enabled)
    db.add(cam)
    db.commit()
    db.refresh(cam)
    return cam

@router.get('/cameras', response_model=list[CameraOut])
def list_cameras(env_id: str, db: Session = Depends(get_db)):
    return db.query(Camera).filter(Camera.env_id == env_id).all()
