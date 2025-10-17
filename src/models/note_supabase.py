from datetime import datetime, date, time
import re
from typing import Optional, Dict, Any
from pydantic import BaseModel
from src.db_config import supabase

class Note(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    tags: Optional[str] = None
    event_date: Optional[date] = None
    event_time: Optional[time] = None  # Changed to time type
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Public normalizers to ensure canonical strings for Supabase
    @staticmethod
    def format_date_str(v) -> Optional[str]:
        if v in (None, '', 'null'):
            return None
        if isinstance(v, date) and not isinstance(v, datetime):
            return v.strftime('%Y-%m-%d')
        if isinstance(v, datetime):
            return v.date().strftime('%Y-%m-%d')
        s = str(v).strip()
        if 'T' in s:
            s = s.split('T')[0]
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(s, fmt).date().strftime('%Y-%m-%d')
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(s).date().strftime('%Y-%m-%d')
        except Exception:
            return None

    @staticmethod
    def format_time_str(v) -> Optional[str]:
        if v in (None, '', 'null'):
            return None
        if isinstance(v, time):
            return v.replace(microsecond=0).strftime('%H:%M:%S')
        if isinstance(v, datetime):
            return v.time().replace(microsecond=0).strftime('%H:%M:%S')
        s = str(v).strip().lower()
        m = re.match(r'^(\d{1,2}):?(\d{2})(?::?(\d{2}))?\s*([ap]\.?.?m\.?)?$', s)
        if m:
            h = int(m.group(1)); mi = int(m.group(2)); sec = int(m.group(3) or 0)
            ampm = m.group(4)
            if ampm:
                if 'p' in ampm and h != 12:
                    h += 12
                if 'a' in ampm and h == 12:
                    h = 0
            h = max(0, min(23, h)); mi = max(0, min(59, mi)); sec = max(0, min(59, sec))
            return f"{h:02d}:{mi:02d}:{sec:02d}"
        try:
            return time.fromisoformat(s).replace(microsecond=0).strftime('%H:%M:%S')
        except Exception:
            return None

    @classmethod
    async def create(cls, title: str, content: str, tags: Optional[str] = None,
                    event_date: Optional[str] = None, event_time: Optional[str] = None) -> 'Note':
        try:
            # Normalize event_date/time to canonical strings for Supabase (DATE/TIME)
            def format_date_str(v) -> Optional[str]:
                if v in (None, '', 'null'):
                    return None
                if isinstance(v, date) and not isinstance(v, datetime):
                    return v.strftime('%Y-%m-%d')
                if isinstance(v, datetime):
                    return v.date().strftime('%Y-%m-%d')
                s = str(v).strip()
                if 'T' in s:
                    s = s.split('T')[0]
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d'):
                    try:
                        return datetime.strptime(s, fmt).date().strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                try:
                    return datetime.fromisoformat(s).date().strftime('%Y-%m-%d')
                except Exception:
                    return None

            def format_time_str(v) -> Optional[str]:
                if v in (None, '', 'null'):
                    return None
                if isinstance(v, time):
                    return v.replace(microsecond=0).strftime('%H:%M:%S')
                if isinstance(v, datetime):
                    return v.time().replace(microsecond=0).strftime('%H:%M:%S')
                s = str(v).strip().lower()
                m = re.match(r'^(\d{1,2}):?(\d{2})(?::?(\d{2}))?\s*([ap]\.?.?m\.?)?$', s)
                if m:
                    h = int(m.group(1)); mi = int(m.group(2)); sec = int(m.group(3) or 0)
                    ampm = m.group(4)
                    if ampm:
                        if 'p' in ampm and h != 12:
                            h += 12
                        if 'a' in ampm and h == 12:
                            h = 0
                    h = max(0, min(23, h)); mi = max(0, min(59, mi)); sec = max(0, min(59, sec))
                    return f"{h:02d}:{mi:02d}:{sec:02d}"
                try:
                    return time.fromisoformat(s).replace(microsecond=0).strftime('%H:%M:%S')
                except Exception:
                    return None

            event_date_str = Note.format_date_str(event_date)
            event_time_str = Note.format_time_str(event_time)
            if event_date and not event_date_str:
                print(f"Invalid date format for event_date: {event_date}")
            if event_time and not event_time_str:
                print(f"Invalid time format for event_time: {event_time}")
            
            # Prepare data for insertion
            now = datetime.utcnow().replace(microsecond=0).isoformat()
            
            data = {
                'title': title,
                'content': content,
                'tags': tags if tags else None,
                'event_date': event_date_str,
                'event_time': event_time_str,
                'created_at': now,
                'updated_at': now
            }
            # Remove None values to avoid sending nulls for non-nullable columns
            payload = {k: v for k, v in data.items() if v is not None}
            
            print(f"Attempting to insert note with payload: {payload}")
            
            try:
                # Insert and force returning the inserted row
                result = supabase.table('notes').insert(payload).execute()
                print(f"Insert response: {result}")
                
                if not result.data:
                    raise ValueError("No data returned from insert operation")
                    
                return_data = result.data[0]
                print(f"Successfully inserted note: {return_data}")
                
                # Convert timestamps back to datetime objects
                if 'created_at' in return_data and isinstance(return_data['created_at'], str):
                    return_data['created_at'] = datetime.fromisoformat(return_data['created_at'].replace('Z', '+00:00'))
                if 'updated_at' in return_data and isinstance(return_data['updated_at'], str):
                    return_data['updated_at'] = datetime.fromisoformat(return_data['updated_at'].replace('Z', '+00:00'))
                    
                return cls(**return_data)
            except Exception as e:
                print(f"Failed to insert note: {str(e)}")
                raise ValueError(f"Failed to insert note: {str(e)}")
            
            note_data = result.data[0] if result.data else None
            if not note_data:
                raise Exception("Failed to create note")
            
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

    async def update(self, title: str = None, content: str = None, tags: str = None,
                    event_date: str = None, event_time: str = None) -> 'Note':
        try:
            update_data: Dict[str, Any] = {'updated_at': datetime.utcnow().replace(microsecond=0).isoformat()}
            if title is not None:
                update_data['title'] = title
            if content is not None:
                update_data['content'] = content
            if tags is not None:
                update_data['tags'] = tags
            if event_date is not None:
                # Reuse the same normalizer from create()
                update_data['event_date'] = Note.format_date_str(event_date)
                if event_date and not update_data['event_date']:
                    print(f"Invalid date format for event_date in update: {event_date}")
            if event_time is not None:
                update_data['event_time'] = Note.format_time_str(event_time)
                if event_time and not update_data['event_time']:
                    print(f"Invalid time format for event_time in update: {event_time}")

            # Remove None fields from update
            update_payload = {k: v for k, v in update_data.items() if v is not None}
            print(f"Executing update for note {self.id} with payload: {update_payload}")
            result = supabase.table('notes').update(update_payload).eq('id', self.id).execute()
            print(f"Update response: {result}")
            if not result.data:
                # Some Supabase Python client versions don't return rows on update; fetch explicitly
                fetched = supabase.table('notes').select('*').eq('id', self.id).limit(1).execute()
                if not fetched.data:
                    raise ValueError('Update succeeded but no data returned')
                updated_data = fetched.data[0]
            else:
                updated_data = result.data[0]
            
            # Convert datetime strings back to datetime objects
            if 'created_at' in updated_data and isinstance(updated_data['created_at'], str):
                updated_data['created_at'] = datetime.fromisoformat(updated_data['created_at'].replace('Z', '+00:00'))
            if 'updated_at' in updated_data and isinstance(updated_data['updated_at'], str):
                updated_data['updated_at'] = datetime.fromisoformat(updated_data['updated_at'].replace('Z', '+00:00'))
                
            return self.__class__(**updated_data)
        except Exception as e:
            print(f"Error updating note: {e}")
            raise

    async def delete(self) -> None:
        supabase.table('notes').delete().eq('id', self.id).execute()

    def to_dict(self) -> Dict[str, Any]:
        # Convert date/time fields to proper strings
        event_date_str = None
        if self.event_date:
            try:
                if isinstance(self.event_date, (date, datetime)):
                    d = self.event_date.date() if isinstance(self.event_date, datetime) else self.event_date
                    event_date_str = d.strftime('%Y-%m-%d')
                else:
                    s = str(self.event_date)
                    if 'T' in s:
                        s = s.split('T')[0]
                    event_date_str = datetime.strptime(s, '%Y-%m-%d').date().strftime('%Y-%m-%d')
            except (ValueError, TypeError) as e:
                print(f"Error formatting event_date in to_dict: {e}")
                event_date_str = str(self.event_date)

        event_time_str = None
        if self.event_time:
            try:
                if isinstance(self.event_time, (time, datetime)):
                    t = self.event_time.time() if isinstance(self.event_time, datetime) else self.event_time
                    event_time_str = t.replace(microsecond=0).strftime('%H:%M:%S')
                else:
                    # assume it's already 'HH:MM[:SS]'
                    s = str(self.event_time)
                    parts = s.split(':')
                    if len(parts) == 2:
                        s = s + ':00'
                    event_time_str = s
            except Exception as e:
                print(f"Error formatting event_time in to_dict: {e}")
                event_time_str = str(self.event_time)
        
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'tags': self.tags,
            'event_date': event_date_str,
            'event_time': event_time_str,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }