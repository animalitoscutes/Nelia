"""
FastAPI Backend Server for Scriptor Studio AI Engine.
Exposes endpoints for:
- Co-writing chat & plot architecture
- Background continuity & story analysis
- Health check and model management
"""

import re
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from ai.config import OLLAMA_BASE_URL, DEFAULT_MODEL, StoryContext
from ai.agents import run_cowriter_chat, run_continuity_analysis

app = FastAPI(title="Scriptor Studio AI Core", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_model_name = DEFAULT_MODEL

class ChatRequest(BaseModel):
    prompt: str
    context: StoryContext
    agent_type: str = "cowriter" # "cowriter" or "architect"
    model: Optional[str] = None
    history: Optional[List[dict]] = None

class ChatResponse(BaseModel):
    reply: str
    suggested_snippet: Optional[str] = None
    agent_used: str
    model_used: str

class ContinuityRequest(BaseModel):
    context: StoryContext
    model: Optional[str] = None

class ContinuityResponse(BaseModel):
    status: str
    report: str
    model_used: str

class ModelSwitchRequest(BaseModel):
    model_name: str

def extract_story_snippet(text: str) -> Optional[str]:
    match = re.search(r"<TEXTO_HISTORIA>(.*?)</TEXTO_HISTORIA>", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

@app.get("/api/status")
async def get_status():
    global active_model_name
    ollama_online = False
    available_models = []

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                ollama_online = True
                data = resp.json()
                available_models = [m["name"] for m in data.get("models", [])]
    except Exception:
        ollama_online = False

    return {
        "status": "online" if ollama_online else "ollama_offline",
        "active_model": active_model_name,
        "ollama_online": ollama_online,
        "gpu": "NVIDIA GeForce RTX 3060 (12GB VRAM)",
        "available_models": available_models,
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    global active_model_name
    model_to_use = req.model or active_model_name
    try:
        reply_text = await run_cowriter_chat(
            prompt=req.prompt,
            context=req.context,
            agent_type=req.agent_type,
            model_name=model_to_use,
            history=req.history or [],
        )
        snippet = extract_story_snippet(reply_text)
        return ChatResponse(
            reply=reply_text,
            suggested_snippet=snippet,
            agent_used=req.agent_type,
            model_used=model_to_use,
        )
    except Exception as e:
        err_msg = str(e)
        if "connect" in err_msg.lower() or "connection" in err_msg.lower():
            err_msg = "No se pudo conectar al servidor local de Ollama (http://localhost:11434). Asegúrate de tener Ollama corriendo ('ollama serve')."
        elif "not found" in err_msg.lower() or ("model" in err_msg.lower() and "404" in err_msg):
            err_msg = f"El modelo '{model_to_use}' no se encontró en tu Ollama. Puedes descargarlo ejecutando 'ollama pull {model_to_use}'."
        raise HTTPException(status_code=500, detail=f"Error en agente de IA: {err_msg}")

@app.post("/api/analyze-continuity", response_model=ContinuityResponse)
async def analyze_continuity_endpoint(req: ContinuityRequest):
    global active_model_name
    model_to_use = req.model or active_model_name
    try:
        report = await run_continuity_analysis(
            context=req.context,
            model_name=model_to_use,
        )
        # Determinar estado
        status = "OK"
        if "Incongruencias Detectadas" in report or "⚠️" in report:
            status = "ATENCION"
        return ContinuityResponse(
            status=status,
            report=report,
            model_used=model_to_use,
        )
    except Exception as e:
        err_msg = str(e)
        if "connect" in err_msg.lower() or "connection" in err_msg.lower():
            err_msg = "Ollama no está activo en localhost:11434. Inicia 'ollama serve' para activar auditorías."
        raise HTTPException(status_code=500, detail=f"Error en auditoría de continuidad: {err_msg}")

@app.post("/api/set-model")
async def set_model_endpoint(req: ModelSwitchRequest):
    global active_model_name
    active_model_name = req.model_name
    return {"message": f"Modelo cambiado a {active_model_name}", "model": active_model_name}

if __name__ == "__main__":
    import uvicorn
    from ai.config import FASTAPI_HOST, FASTAPI_PORT
    uvicorn.run(app, host=FASTAPI_HOST, port=FASTAPI_PORT)
