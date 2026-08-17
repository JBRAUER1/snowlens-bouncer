from pydantic import BaseModel
from typing import List, Dict, Optional

class StyleRequest(BaseModel):
    ai_model: str
    stats: dict
    genre_tags: list = []
    profile: str = ""
    api_key: str  # Catches the 'login_key' sent by the desktop app

class CoachPreflightRequest(BaseModel):
    chunk_text: str
    ai_model: str
    api_key: str

class CoachMainRequest(BaseModel):
    chunk_text: str
    narrative_context: str
    constraints: str
    limit: int
    ai_model: str
    api_key: str

class PassRequest(BaseModel):
    chunk_text: str
    active_tool: str
    constraints: str
    limit: int
    exclusion: str
    ai_model: str
    api_key: str

class AdjudicatorRequest(BaseModel):
    manuscript_snippet: str
    critiques_list: str
    ai_model: str
    api_key: str