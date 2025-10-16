from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from src.db_config import supabase

class Note(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    async def create(cls, title: str, content: str) -> 'Note':
        data = {
            'title': title,
            'content': content,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('notes').insert(data).execute()
        note_data = result.data[0]
        return cls(**note_data)

    @classmethod
    async def get_all(cls) -> list['Note']:
        result = supabase.table('notes').select('*').execute()
        return [cls(**note) for note in result.data]

    @classmethod
    async def get_by_id(cls, note_id: str) -> Optional['Note']:
        result = supabase.table('notes').select('*').eq('id', note_id).execute()
        if not result.data:
            return None
        return cls(**result.data[0])

    async def update(self, title: str = None, content: str = None) -> 'Note':
        update_data: Dict[str, Any] = {'updated_at': datetime.utcnow().isoformat()}
        if title is not None:
            update_data['title'] = title
        if content is not None:
            update_data['content'] = content

        result = supabase.table('notes').update(update_data).eq('id', self.id).execute()
        updated_data = result.data[0]
        return self.__class__(**updated_data)

    async def delete(self) -> None:
        supabase.table('notes').delete().eq('id', self.id).execute()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }