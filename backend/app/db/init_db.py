from app.db.database import engine
from app.db.base import Base

# import models so SQLAlchemy registers them
from app.models.core import Organization, User, Environment, Camera  # noqa: F401

def init_db():
    Base.metadata.create_all(bind=engine)
