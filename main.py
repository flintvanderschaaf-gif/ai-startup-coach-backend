from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
import httpx
import os
import json
import re

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

class AnswerInput(BaseModel):
    tijd: str
    skill: str
    budget: str
    inkomen: str
    grootte: str

@app.get("/")
def root():
    return {"status": "AI Startup Coach backend actief"}

@app.post("/analyse")
@limiter.limit("5/minute")
async def analyse(data: AnswerInput, request: Request):
    prompt = f"""
Je bent een startup coach voor tieners in Nederland en België.
Een gebruiker heeft deze antwoorden gegeven:
- Beschikbare tijd per week: {data.tijd}
- Sterkste skill: {data.skill}
- Startbudget: {data.budget}
- Gewenst inkomen type: {data.inkomen}
- Ambitie: {data.grootte}

Geef ALLEEN een JSON response zonder uitleg of markdown:
{{"score": 85, "idee": "AI Tool Builder", "beschrijving": "2 zinnen waarom dit past.", "tags": ["Online", "Gratis", "Passief"], "eerste_stap": "1 concrete actie vandaag"}}
"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-8b-8192",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                    "temperature": 0.7
                },
                timeout=20
            )

        result = response.json()
        print("Groq response:", result)  # debug log

        text = result["choices"][0]["message"]["content"]
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            return {"score": 80, "idee": "AI Content Creator", "beschrijving": "Past goed bij jou.", "tags": ["Online", "Gratis", "Passief"], "eerste_stap": "Maak vandaag een gratis Groq account aan."}

    except Exception as e:
        print("ERROR:", str(e))
        return {"score": 80, "idee": "AI Content Creator", "beschrijving": "Past goed bij jou.", "tags": ["Online", "Gratis", "Passief"], "eerste_stap": "Maak vandaag een gratis Groq account aan."}
