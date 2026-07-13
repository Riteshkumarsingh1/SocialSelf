from fastapi import APIRouter, Request, HTTPException, Depends
from .ai_agent import get_ai_response, get_user_tone
from .database import get_db
from .auth import get_current_user

router = APIRouter()

@router.post("/chat")
async def chat(request: Request, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    user_message = data.get("message", "")
    
    user_id = current_user.get("user_id")
    tone = await get_user_tone(user_id)
    
    # Get previous chat context (last 5 messages)
    context = []
    async with get_db() as db:
        async with db.execute(
            "SELECT message, ai_reply FROM chat_messages WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            # rows is list of tuples (message, ai_reply)
            for row in reversed(rows):
                context.append({"role": "user", "content": row[0]})
                context.append({"role": "assistant", "content": row[1]})
    
    ai_reply = await get_ai_response(user_message, tone, context)
    
    # Save to database
    async with get_db() as db:
        await db.execute(
            "INSERT INTO chat_messages (user_id, message, ai_reply, tone_used) VALUES (?, ?, ?, ?)",
            (user_id, user_message, ai_reply, tone)
        )
        await db.commit()
    
    return {"reply": ai_reply}

@router.get("/chat/history")
async def get_chat_history(current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = current_user.get("user_id")
    async with get_db() as db:
        async with db.execute(
            "SELECT message, ai_reply, tone_used, created_at FROM chat_messages WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
    
    return [{"message": r[0], "reply": r[1], "tone": r[2], "timestamp": r[3]} for r in rows]