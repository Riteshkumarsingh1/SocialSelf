from fastapi import APIRouter, HTTPException, Request, Response, Form
from passlib.context import CryptContext
from jose import jwt
import datetime
import os
from .database import get_db

router = APIRouter()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "my-super-secret-key-change-this")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_token(user_id: int, email: str):
    return jwt.encode(
        {"user_id": user_id, "email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
        SECRET_KEY,
        algorithm="HS256"
    )

async def get_current_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        return None

@router.post("/register")
async def register(name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    hashed = hash_password(password)
    async with get_db() as db:
        try:
            await db.execute(
                "INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)",
                (name, email, hashed)
            )
            await db.commit()
            return {"status": "success", "message": "User registered successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail="Email already exists")

@router.post("/login")
async def login(response: Response, email: str = Form(...), password: str = Form(...)):
    async with get_db() as db:
        async with db.execute("SELECT id, name, email, hashed_password FROM users WHERE email = ?", (email,)) as cursor:
            user = await cursor.fetchone()
    
    if not user or not verify_password(password, user[3]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user[0], user[2])
    response.set_cookie(key="token", value=token, httponly=True)
    return {"status": "success", "user": {"id": user[0], "name": user[1], "email": user[2]}}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("token")
    return {"status": "success"}