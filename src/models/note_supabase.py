from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from src.db_config import supabase

#test
class Note(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    async def create(cls, title: str, content: str) -> 'Note':
        try:
            data = {
                'title': title,
                'content': content,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = supabase.table('notes').insert(data).execute()
            note_data = result.data[0]
            # Convert datetime strings back to datetime objects
            if 'created_at' in note_data:
                note_data['created_at'] = datetime.fromisoformat(note_data['created_at'].replace('Z', '+00:00'))
            if 'updated_at' in note_data:
                note_data['updated_at'] = datetime.fromisoformat(note_data['updated_at'].replace('Z', '+00:00'))
            return cls(**note_data)
        except Exception as e:
            print(f"Error creating note: {e}")
            raise

    @classmethod
    async def get_all(cls) -> list['Note']:
        try:
            result = supabase.table('notes').select('*').execute()
            notes = []
            for note_data in result.data:
                # Convert datetime strings back to datetime objects
                if 'created_at' in note_data:
                    note_data['created_at'] = datetime.fromisoformat(note_data['created_at'].replace('Z', '+00:00'))
                if 'updated_at' in note_data:
                    note_data['updated_at'] = datetime.fromisoformat(note_data['updated_at'].replace('Z', '+00:00'))
                notes.append(cls(**note_data))
            return notes
        except Exception as e:
            print(f"Error getting all notes: {e}")
            raise

    @classmethod
    async def get_by_id(cls, note_id: str) -> Optional['Note']:
        try:
            result = supabase.table('notes').select('*').eq('id', note_id).execute()
            if not result.data:
                return None
            note_data = result.data[0]
            # Convert datetime strings back to datetime objects
            if 'created_at' in note_data:
                note_data['created_at'] = datetime.fromisoformat(note_data['created_at'].replace('Z', '+00:00'))
            if 'updated_at' in note_data:
                note_data['updated_at'] = datetime.fromisoformat(note_data['updated_at'].replace('Z', '+00:00'))
            return cls(**note_data)
        except Exception as e:
            print(f"Error getting note by ID: {e}")
            raise

    async def update(self, title: str = None, content: str = None) -> 'Note':
        try:
            update_data: Dict[str, Any] = {'updated_at': datetime.utcnow().isoformat()}
            if title is not None:
                update_data['title'] = title
            if content is not None:
                update_data['content'] = content

            result = supabase.table('notes').update(update_data).eq('id', self.id).execute()
            updated_data = result.data[0]
            
            # Convert datetime strings back to datetime objects
            if 'created_at' in updated_data:
                updated_data['created_at'] = datetime.fromisoformat(updated_data['created_at'].replace('Z', '+00:00'))
            if 'updated_at' in updated_data:
                updated_data['updated_at'] = datetime.fromisoformat(updated_data['updated_at'].replace('Z', '+00:00'))
                
            return self.__class__(**updated_data)
        except Exception as e:
            print(f"Error updating note: {e}")
            raise

    async def delete(self) -> None:
        supabase.table('notes').delete().eq('id', self.id).execute()

    def to_dict(self) -> dict:
        return {
            'id': str(self.id) if self.id is not None else None,  # Ensure ID is a string
            'title': str(self.title) if self.title is not None else '',
            'content': str(self.content) if self.content is not None else '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }