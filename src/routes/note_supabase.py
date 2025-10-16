from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from src.models.note_supabase import Note

router = APIRouter()

class NoteCreate(BaseModel):
    title: str
    content: str

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

@router.post("/notes/", response_model=dict)
async def create_note(note: NoteCreate):
    created_note = await Note.create(title=note.title, content=note.content)
    return created_note.to_dict()

@router.get("/notes/", response_model=List[dict])
async def get_notes():
    notes = await Note.get_all()
    return [note.to_dict() for note in notes]

@router.get("/notes/{note_id}", response_model=dict)
async def get_note(note_id: str):
    note = await Note.get_by_id(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note.to_dict()

@router.put("/notes/{note_id}", response_model=dict)
async def update_note(note_id: str, note: NoteUpdate):
    existing_note = await Note.get_by_id(note_id)
    if existing_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    updated_note = await existing_note.update(title=note.title, content=note.content)
    return updated_note.to_dict()

@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    note = await Note.get_by_id(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    await note.delete()
    return {"message": "Note deleted successfully"}