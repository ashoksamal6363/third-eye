import os, time, jwt, hashlib

JWT_SECRET = os.getenv("JWT_SECRET", "change_me")

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def sign_token(user_id: str, org_id: str, role: str) -> str:
    payload = {"sub": user_id, "org": org_id, "role": role, "iat": int(time.time())}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
