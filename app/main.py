from fastapi import FastAPI, Request, Form, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SocialSelf - AI Communication Agent")

# ========== SIMPLE TEST ENDPOINT (FIRST, TO TEST WEBHOOK) ==========
@app.post("/test-call")
async def test_call():
    from fastapi.responses import Response
    return Response(
        content='<Response><Say>Hello! This is a test. Your webhook works.</Say></Response>',
        media_type="application/xml"
    )
# ====================================================================

# Now imports from your app modules (must be after app is defined)
from .database import init_db
from .auth import router as auth_router, get_current_user
from .ai_agent import get_ai_response, get_user_tone, update_user_tone, TONES
from .twilio_voice import router as voice_router
from .whatsapp import router as whatsapp_router
from .chat import router as chat_router

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(voice_router, prefix="/api", tags=["voice"])
app.include_router(whatsapp_router, prefix="/api", tags=["whatsapp"])
app.include_router(chat_router, prefix="/api", tags=["chat"])

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
async def root():
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - SocialSelf</title>
        <style>
            body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
            .card { background: white; padding: 40px; border-radius: 20px; width: 350px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
            h1 { text-align: center; color: #333; margin-bottom: 30px; }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; }
            button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; }
            .switch { text-align: center; margin-top: 15px; }
            .switch a { color: #667eea; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🔐 SocialSelf</h1>
            <form id="login-form">
                <input type="email" id="email" placeholder="Email" required>
                <input type="password" id="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <div class="switch">Don't have an account? <a href="/register">Register</a></div>
        </div>
        <script>
            document.getElementById('login-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new URLSearchParams();
                formData.append('email', document.getElementById('email').value);
                formData.append('password', document.getElementById('password').value);
                const response = await fetch('/api/login', { method: 'POST', body: formData });
                if (response.ok) window.location.href = '/dashboard';
                else alert('Login failed');
            });
        </script>
    </body>
    </html>
    """

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register - SocialSelf</title>
        <style>
            body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
            .card { background: white; padding: 40px; border-radius: 20px; width: 350px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
            h1 { text-align: center; color: #333; margin-bottom: 30px; }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; }
            button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; }
            .switch { text-align: center; margin-top: 15px; }
            .switch a { color: #667eea; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📝 Create Account</h1>
            <form id="register-form">
                <input type="text" id="name" placeholder="Full Name" required>
                <input type="email" id="email" placeholder="Email" required>
                <input type="password" id="password" placeholder="Password" required>
                <button type="submit">Register</button>
            </form>
            <div class="switch">Already have an account? <a href="/login">Login</a></div>
        </div>
        <script>
            document.getElementById('register-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new URLSearchParams();
                formData.append('name', document.getElementById('name').value);
                formData.append('email', document.getElementById('email').value);
                formData.append('password', document.getElementById('password').value);
                const response = await fetch('/api/register', { method: 'POST', body: formData });
                if (response.ok) window.location.href = '/login';
                else alert('Registration failed');
            });
        </script>
    </body>
    </html>
    """

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    
    try:
        with open("app/templates/dashboard.html", "r", encoding="utf-8") as f:
            html = f.read()
        return HTMLResponse(content=html)
    except FileNotFoundError:
        return HTMLResponse(content="<h2>Dashboard template not found. Please check app/templates/dashboard.html</h2>", status_code=404)

@app.post("/api/set-tone")
async def set_user_tone(request: Request, tone: str = Form(...)):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if tone in TONES:
        await update_user_tone(user["user_id"], tone)
        return {"status": "success", "tone": tone}
    return {"status": "error", "message": "Invalid tone"}

@app.get("/api/user")
async def get_user(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"id": user["user_id"], "name": user.get("name", "User"), "email": user["email"]}

@app.post("/api/logout")
async def logout_user(response: Response):
    response.delete_cookie("token")
    return {"status": "success"}