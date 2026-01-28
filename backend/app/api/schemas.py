from pydantic import BaseModel
from typing import Optional

class OrgCreate(BaseModel):
    name: str

class OrgOut(BaseModel):
    id: str
    name: str

class EnvCreate(BaseModel):
    org_id: str
    name: str
    region: Optional[str] = None

class EnvOut(BaseModel):
    id: str
    org_id: str
    name: str
    region: Optional[str] = None

class CameraCreate(BaseModel):
    env_id: str
    name: str
    rtsp_url: str
    enabled: bool = True

class CameraOut(BaseModel):
    id: str
    env_id: str
    name: str
    rtsp_url: str
    enabled: bool
