from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from src.models.note_supabase import Note
from src.db_config import init_supabase_if_needed

router = APIRouter()

class NoteCreate(BaseModel):
    title: str
    content: str
    tags: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None

@router.post("/notes", response_model=dict)
async def create_note(note: NoteCreate):
    if not init_supabase_if_needed():
        raise HTTPException(status_code=503, detail="Database not configured. Set SUPABASE_URL and SUPABASE_KEY.")
    # Normalize tags: accept CSV string or list and send as CSV string to Supabase
    tags = note.tags
    if isinstance(tags, list):
        tags = ",".join(t.strip() for t in tags if t)
    created_note = await Note.create(
        title=note.title or "Untitled",
        content=note.content or "",
        tags=tags,
        event_date=note.event_date,
        event_time=note.event_time,
    )
    return created_note.to_dict()

@router.get("/notes", response_model=List[dict])
async def get_notes():
    if not init_supabase_if_needed():
        raise HTTPException(status_code=503, detail="Database not configured. Set SUPABASE_URL and SUPABASE_KEY.")
    notes = await Note.get_all()
    return [note.to_dict() for note in notes]

@router.get("/notes/{note_id}", response_model=dict)
async def get_note(note_id: str):
    if not init_supabase_if_needed():
        raise HTTPException(status_code=503, detail="Database not configured. Set SUPABASE_URL and SUPABASE_KEY.")
    note = await Note.get_by_id(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note.to_dict()

@router.put("/notes/{note_id}", response_model=dict)
async def update_note(note_id: str, note: NoteUpdate):
    if not init_supabase_if_needed():
        raise HTTPException(status_code=503, detail="Database not configured. Set SUPABASE_URL and SUPABASE_KEY.")
    existing_note = await Note.get_by_id(note_id)
    if existing_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    tags = note.tags
    if isinstance(tags, list):
        tags = ",".join(t.strip() for t in tags if t)
    updated_note = await existing_note.update(
        title=note.title,
        content=note.content,
        tags=tags,
        event_date=note.event_date,
        event_time=note.event_time,
    )
    return updated_note.to_dict()

@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    if not init_supabase_if_needed():
        raise HTTPException(status_code=503, detail="Database not configured. Set SUPABASE_URL and SUPABASE_KEY.")
    note = await Note.get_by_id(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    await note.delete()
    return {"message": "Note deleted successfully"}