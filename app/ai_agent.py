import os
from groq import Groq
from dotenv import load_dotenv
from .database import get_db

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Tone configurations
TONES = {
    "polite": "You are a polite, respectful assistant. Use 'please' and 'thank you'. Be warm and courteous.",
    "aggressive": "You are direct, assertive, and confident. Get to the point quickly. No small talk. Be blunt but professional.",
    "humble": "You are humble and modest. Speak softly, acknowledge limitations, show gratitude. Don't boast.",
    "sentimental": "You are warm, emotional, and caring. Show deep empathy. Use heartfelt language.",
    "friendly": "You are casual, friendly, and approachable. Use contractions. Smile while speaking.",
    "professional": "You are a formal, business-appropriate assistant. Use proper language. Be concise and respectful.",
    "sarcastic": "You are witty and ironic. Use subtle sarcasm. Keep it light-hearted, not mean."
}

async def get_ai_response(user_message: str, tone: str, context: list = None) -> str:
    """
    Get response from Groq API with tone control.
    Returns string response.
    """
    system_prompt = f"{TONES.get(tone, TONES['friendly'])} Keep responses brief and natural. Reply as the user's assistant."
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation context if available
    if context:
        messages.extend(context[-5:])  # Last 5 messages for context
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",  # Fastest model on Groq
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"I apologize, but I'm having trouble responding right now. Please try again."

async def update_user_tone(user_id: int, tone: str) -> bool:
    """Update user's current tone in database (SQLite version)"""
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET current_tone = ? WHERE id = ?",
            (tone, user_id)
        )
        await db.commit()
    return True

async def get_user_tone(user_id: int) -> str:
    """Get user's current tone from database (SQLite version)"""
    async with get_db() as db:
        async with db.execute("SELECT current_tone FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
    return row[0] if row else "friendly"
