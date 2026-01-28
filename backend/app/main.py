from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.init_db import init_db
from app.models.core import Organization

app = FastAPI(title='Third Eye API')

@app.on_event('startup')
def on_startup():
    init_db()

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/orgs')
def create_org(name: str, db: Session = Depends(get_db)):
    org = Organization(name=name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return {'id': org.id, 'name': org.name}

@app.get('/orgs')
def list_orgs(db: Session = Depends(get_db)):
    rows = db.query(Organization).order_by(Organization.created_at.desc()).all()
    return [{'id': o.id, 'name': o.name} for o in rows]
