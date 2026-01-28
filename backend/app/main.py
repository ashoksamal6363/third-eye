from fastapi import FastAPI
from app.db.init_db import init_db
from app.api.routes import router

app = FastAPI(title='Third Eye API')

@app.on_event('startup')
def on_startup():
    init_db()

@app.get('/health')
def health():
    return {'status': 'ok'}

app.include_router(router)
