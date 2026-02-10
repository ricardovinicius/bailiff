import logging
from datetime import datetime
from sqlalchemy.orm import Session

from bailiff.core.db import init_db
from bailiff.features.memory.models import Sessions, Transcripts
from bailiff.core.events import TranscriptionSegment

logger = logging.getLogger("bailiff.storage")

class MeetingStorage:
    def __init__(self, db: Session):
        self.db = db
        init_db()  # Ensure tables exist

    def create_session(self, name: str | None = None) -> Sessions:
        """Create a new meeting session."""
        if name is None:
            name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
        session = Sessions(
            name=name,
            start_time=datetime.now()
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        logger.info("Created session: %s (id=%d)", session.name, session.id)
        return session

    def save_transcript(self, session_id: int, segment: TranscriptionSegment) -> Transcripts:
        """Save a transcription segment to the database."""
        transcript = Transcripts(
            session_id=session_id,
            text=segment.text,
            start_time=segment.start_time,
            end_time=segment.end_time,
            speaker=segment.speaker
        )
        self.db.add(transcript)
        self.db.commit()
        logger.debug("Saved transcript segment for session %d", session_id)
        return transcript

    def get_sessions(self):
        return self.db.query(Sessions).order_by(Sessions.start_time.desc()).all()

    def get_transcripts(self, session_id: int):
        return self.db.query(Transcripts).filter(Transcripts.session_id == session_id).order_by(Transcripts.start_time).all()

    def get_session(self, session_id: int) -> Sessions | None:
        """Get a session by ID."""
        return self.db.query(Sessions).filter(Sessions.id == session_id).first()