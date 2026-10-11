"""
AI Engine Configuration.
Targets local Ollama on RTX 3060 (12GB VRAM) via OpenAI-compatible API.
"""

import os
from pydantic import BaseModel

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
DEFAULT_MODEL = os.getenv("AI_MODEL", "qwen2.5:7b") # Premier creative writing model on RTX 3060
FASTAPI_PORT = int(os.getenv("SCRIPT_AI_PORT", 8765))
FASTAPI_HOST = "127.0.0.1"

class StoryContext(BaseModel):
    title: str = "Sin Título"
    current_scene_title: str = ""
    current_text: str = ""
    selected_text: str = ""
    mode: str = "screenplay" # "screenplay" or "novel"
    characters: list[str] = []
    author_prompt: str = ""
