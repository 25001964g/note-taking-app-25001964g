from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
import re
from src.models.user import db

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(200), nullable=True)
    event_date = db.Column(db.Date, nullable=True)
    event_time = db.Column(db.Time, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Note {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'tags': [t.strip() for t in self.tags.split(',')] if self.tags else [],
            # Emit canonical formats for the frontend
            'event_date': self.event_date.strftime('%Y-%m-%d') if self.event_date else None,
            'event_time': self.event_time.strftime('%H:%M:%S') if self.event_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    # ---- Helpers to parse incoming strings into PostgreSQL-ready Python values ----
    @staticmethod
    def parse_date(value):
        """Accept various inputs and return a date or None.
        Supported formats:
        - YYYY-MM-DD (preferred)
        - DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY, YYYY/MM/DD
        - ISO strings with time (only date part used)
        - datetime/date objects passthrough
        """
        if value in (None, '', 'null'):
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        v = str(value).strip()
        # Trim time portion if present (e.g., 2025-10-17T00:00:00Z)
        if 'T' in v:
            v = v.split('T')[0]
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(v, fmt).date()
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(v).date()
        except Exception:
            return None

    @staticmethod
    def parse_time(value):
        """Accept HH:MM, HH:MM:SS, or 12h like '2:43 pm'; return time or None.
        Ensures seconds and no microseconds for PostgreSQL TIME.
        """
        if value in (None, '', 'null'):
            return None
        if isinstance(value, time):
            return value.replace(microsecond=0)
        if isinstance(value, datetime):
            return value.time().replace(microsecond=0)

        v = str(value).strip().lower()
        # Match 12/24h, optional ':' between h and m, optional seconds, optional am/pm
        m = re.match(r'^(\d{1,2}):?(\d{2})(?::?(\d{2}))?\s*([ap]\.?.?m\.?)?$', v)
        if m:
            h = int(m.group(1))
            mi = int(m.group(2))
            s = int(m.group(3) or 0)
            ampm = m.group(4)
            if ampm:
                if 'p' in ampm and h != 12:
                    h += 12
                if 'a' in ampm and h == 12:
                    h = 0
            # Clamp to valid ranges
            h = max(0, min(23, h))
            mi = max(0, min(59, mi))
            s = max(0, min(59, s))
            return time(hour=h, minute=mi, second=s)

        try:
            t = time.fromisoformat(v)
            return t.replace(microsecond=0)
        except Exception:
            return None

    # ---- Convenient creators/updaters for routes/services ----
    @classmethod
    def create_from_dict(cls, data):
        """Create a Note instance from request-like dict, parsing/normalizing fields."""
        tags_val = data.get('tags')
        if isinstance(tags_val, list):
            tags_str = ','.join([str(t).strip() for t in tags_val if str(t).strip()])
        else:
            tags_str = (str(tags_val).strip() if tags_val else None)

        return cls(
            title=(data.get('title') or '').strip(),
            content=(data.get('content') or '').strip(),
            tags=tags_str or None,
            event_date=cls.parse_date(data.get('event_date')),
            event_time=cls.parse_time(data.get('event_time')),
        )

    def update_from_dict(self, data):
        if 'title' in data:
            self.title = (data.get('title') or '').strip()
        if 'content' in data:
            self.content = (data.get('content') or '').strip()
        if 'tags' in data:
            tags_val = data.get('tags')
            if isinstance(tags_val, list):
                tags_str = ','.join([str(t).strip() for t in tags_val if str(t).strip()])
            else:
                tags_str = (str(tags_val).strip() if tags_val else None)
            self.tags = tags_str or None
        if 'event_date' in data:
            self.event_date = self.parse_date(data.get('event_date'))
        if 'event_time' in data:
            self.event_time = self.parse_time(data.get('event_time'))
        self.updated_at = datetime.utcnow()

