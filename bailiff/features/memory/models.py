from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Sessions(Base):
    """
    SQLAlchemy model representing a meeting session.
    """
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    transcripts = relationship("Transcripts", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session(id={self.id}, name='{self.name}')>"

class Transcripts(Base):
    """
    SQLAlchemy model representing a specific segment of transcription.
    """
    __tablename__ = "transcripts"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    text = Column(String)
    start_time = Column(Float) # changed from DateTime to Float to match audio timestamps
    end_time = Column(Float)   # changed from DateTime to Float
    speaker = Column(String)
    
    session = relationship("Sessions", back_populates="transcripts")

    def __repr__(self):
        return f"<Transcript(id={self.id}, text='{(self.text or '')[:20]}...')>"