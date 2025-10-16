from datetime import datetime, date, time
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

    @classmethod
    async def create(cls, title: str, content: str, tags: Optional[str] = None,
                    event_date: Optional[str] = None, event_time: Optional[str] = None) -> 'Note':
        try:
            # Handle event_date for Supabase date type
            event_date_obj = None
            if event_date:
                try:
                    # If already a date object
                    if isinstance(event_date, date):
                        event_date_obj = event_date
                    # If datetime object
                    elif isinstance(event_date, datetime):
                        event_date_obj = event_date.date()
                    # If string
                    elif isinstance(event_date, str):
                        # Remove any timezone info or time part
                        clean_date = event_date.split('T')[0] if 'T' in event_date else event_date
                        # Parse to date object
                        event_date_obj = datetime.strptime(clean_date, '%Y-%m-%d').date()
                    
                    print(f"Successfully converted date {event_date} to date object: {event_date_obj}")
                except (ValueError, TypeError) as e:
                    print(f"Invalid date format for event_date: {event_date}. Error: {str(e)}")
                    event_date_obj = None
            
            # Handle event_time for SQL TIME type
            event_time_obj = None
            if event_time:
                try:
                    # If already a time object
                    if isinstance(event_time, time):
                        event_time_obj = event_time
                    # If string (handle different formats)
                    elif isinstance(event_time, str):
                        # Try different time formats
                        formats = ['%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M%p']
                        for fmt in formats:
                            try:
                                parsed_time = datetime.strptime(event_time, fmt)
                                event_time_obj = parsed_time.time()
                                break
                            except ValueError:
                                continue
                        if not event_time_obj:
                            raise ValueError(f"Could not parse time: {event_time}")
                    
                    print(f"Successfully converted time {event_time} to time object: {event_time_obj}")
                except (ValueError, TypeError) as e:
                    print(f"Invalid time format for event_time: {event_time}. Error: {str(e)}")
                    event_time_obj = None
            
            # Prepare data for insertion
            now = datetime.utcnow().isoformat()
            
            data = {
                'title': title,
                'content': content,
                'tags': tags if tags else None,
                'event_date': event_date_obj.isoformat() if event_date_obj else None,
                'event_time': event_time_obj.strftime('%H:%M:%S') if event_time_obj else None,
                'created_at': now,
                'updated_at': now
            }
            
            print(f"Attempting to insert note with data: {data}")
            
            try:
                # Insert directly using Supabase client
                result = supabase.table('notes').insert(data).execute()
                print(f"Insert response: {result}")
                
                if not result.data:
                    raise ValueError("No data returned from insert operation")
                    
                return_data = result.data[0]
                print(f"Successfully inserted note: {return_data}")
                
                # Convert timestamps back to datetime objects
                if 'created_at' in return_data:
                    return_data['created_at'] = datetime.fromisoformat(return_data['created_at'].replace('Z', '+00:00'))
                if 'updated_at' in return_data:
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
            update_data: Dict[str, Any] = {'updated_at': datetime.utcnow().isoformat()}
            if title is not None:
                update_data['title'] = title
            if content is not None:
                update_data['content'] = content
            if tags is not None:
                update_data['tags'] = tags
            if event_date is not None:
                try:
                    if isinstance(event_date, str):
                        event_date = event_date.split('T')[0]  # Take only the date part
                        parsed_date = datetime.strptime(event_date, '%Y-%m-%d')
                    else:
                        parsed_date = event_date
                    
                    update_data['event_date'] = parsed_date.date().isoformat()
                    print(f"Successfully parsed update date {event_date} to {update_data['event_date']}")
                except (ValueError, TypeError) as e:
                    print(f"Invalid date format for event_date: {event_date}. Error: {str(e)}")
                    update_data['event_date'] = None
            if event_time is not None:
                update_data['event_time'] = event_time

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

    def to_dict(self) -> Dict[str, Any]:
        # Convert date fields to proper format
        event_date_str = None
        if self.event_date:
            try:
                if isinstance(self.event_date, datetime):
                    event_date_str = self.event_date.date().isoformat()
                else:
                    clean_date = self.event_date.split('T')[0] if 'T' in self.event_date else self.event_date
                    parsed_date = datetime.strptime(clean_date, '%Y-%m-%d')
                    event_date_str = parsed_date.date().isoformat()
            except (ValueError, TypeError) as e:
                print(f"Error formatting event_date in to_dict: {e}")
                event_date_str = self.event_date
        
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'tags': self.tags,
            'event_date': event_date_str,
            'event_time': self.event_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }