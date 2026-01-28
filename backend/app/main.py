from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.init_db import init_db
from app.api.routes import router

app = FastAPI(title='Third Eye API')

# allow Next.js local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event('startup')
def on_startup():
    init_db()

@app.get('/health')
def health():
    return {'status': 'ok'}

app.include_router(router)
