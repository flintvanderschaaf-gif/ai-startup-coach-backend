from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
import httpx
import os

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

Geef een JSON response met exact deze velden (geen uitleg, alleen JSON):
{{
  "score": <getal tussen 70 en 99>,
  "idee": "<naam van het businessidee, max 4 woorden>",
  "beschrijving": "<2 zinnen uitleg waarom dit past bij deze persoon>",
  "tags": ["<tag1>", "<tag2>", "<tag3>"],
  "eerste_stap": "<1 concrete actie die ze vandaag kunnen doen>"
}}
"""

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
            timeout=15
        )

    result = response.json()
    text = result["choices"][0]["message"]["content"]

    # Parse JSON from response
    import json, re
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        data_out = json.loads(match.group())
        return data_out
    else:
        return {"score": 80, "idee": "AI Content Creator", "beschrijving": "Past goed bij jou.", "tags": ["Online", "Gratis"], "eerste_stap": "Maak een gratis Groq account aan."}
