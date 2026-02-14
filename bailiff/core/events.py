from dataclasses import dataclass
import numpy as np

@dataclass
class AudioChunk:
    """
    Standard unit of audio passed between processes.
    """
    data: np.ndarray    
    sample_rate: int
    timestamp: float
    duration: float
    is_speech: bool = True

@dataclass
class TranscriptionSegment:
    """
    A segment of audio that has been transcribed.
    """
    text: str
    start_time: float
    end_time: float
    duration: float
    speaker: str = "unknown"
    is_final: bool = True

@dataclass
class SearchRequest:
    """
    Request to search the vector database.
    """
    query: str
    session_id: str
    k: int = 5

@dataclass
class DiarizationResult:
    """
    Result of a diarization process for a specific audio segment.
    """
    speaker: str
    start_time: float
    end_time: float

