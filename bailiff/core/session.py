import multiprocessing
import queue
import threading
import logging

from bailiff.features.audio_ingest.service import run_ingest_service
from bailiff.features.transcription.service import run_transcription_service
from bailiff.features.diarization.service import run_diarization_service
from bailiff.features.diarization.merge import run_merge_service
from bailiff.features.memory.service import run_memory_service
from bailiff.features.assistant.service import run_assistant_service
from bailiff.features.memory.storage import MeetingStorage
from bailiff.core.db import SessionLocal
from bailiff.core.config import AudioConfig

logger = logging.getLogger("bailiff.core.session")

class SessionManager:
    def __init__(self, log_file="bailiff.log"):
        self.log_file = log_file
        
        # Queues
        self.q_audio_raw = multiprocessing.Queue()    # ingest output
        self.q_audio_tx = multiprocessing.Queue()     # copy for transcription
        self.q_audio_diar = multiprocessing.Queue()   # copy for diarization

        self.q_text = multiprocessing.Queue()          # transcription output
        self.q_diarization = multiprocessing.Queue()   # diarization output
        self.q_merged = multiprocessing.Queue()        # merge output -> UI

        self.q_memory = multiprocessing.Queue()
        self.q_question = multiprocessing.Queue()
        self.q_answer = multiprocessing.Queue()
        self.q_rag = multiprocessing.Queue()
        
        # Session ID initialization
        self.session_id = self._create_session()
        
        self._fanout_stop = threading.Event()
        self.processes = []
        self._fanout_thread = None

    def _create_session(self):
        db = SessionLocal()
        try:
            storage = MeetingStorage(db)
            session = storage.create_session()
            return session.id
        finally:
            db.close()

    def _audio_fanout(self):
        """
        Duplicate audio chunks from ingest to both transcription and diarization queues.
        """
        while not self._fanout_stop.is_set():
            try:
                chunk = self.q_audio_raw.get(timeout=0.5)
            except queue.Empty:
                continue
            self.q_audio_tx.put(chunk)
            self.q_audio_diar.put(chunk)
            if chunk is None:
                break  # poison pill forwarded to both consumers

    def start(self):
        """
        Start all background processes and the fanout thread.
        """
        # Fan-out thread
        self._fanout_thread = threading.Thread(
            target=self._audio_fanout, daemon=True, name="audio-fanout"
        )
        self._fanout_thread.start()

        # Processes
        self.processes = [
            multiprocessing.Process(
                target=run_ingest_service,
                args=(self.q_audio_raw, AudioConfig(), self.log_file),
                daemon=True,
                name="audio-ingest",
            ),
            multiprocessing.Process(
                target=run_transcription_service,
                args=(self.q_audio_tx, self.q_text, self.log_file),
                daemon=True,
                name="transcription",
            ),
            multiprocessing.Process(
                target=run_diarization_service,
                args=(self.q_audio_diar, self.q_diarization, self.log_file),
                daemon=True,
                name="diarization",
            ),
            multiprocessing.Process(
                target=run_merge_service,
                args=(self.q_text, self.q_diarization, self.q_merged, self.log_file),
                daemon=True,
                name="merge",
            ),
            multiprocessing.Process(
                target=run_memory_service,
                args=(self.q_memory, self.q_rag, self.session_id, self.log_file),
                daemon=True,
                name="memory",
            ),
            multiprocessing.Process(
                target=run_assistant_service,
                args=(self.q_question, self.q_answer, self.q_memory, self.q_rag, self.session_id, self.log_file),
                daemon=True,
                name="assistant",
            ),
        ]

        for p in self.processes:
            p.start()
            
    def stop(self):
        """
        Stop all processes and threads, and close queues.
        """
        self._fanout_stop.set()
        
        for p in self.processes:
            if p.is_alive():
                p.terminate()
                
        # Close queues
        for q in [
            self.q_audio_raw, self.q_audio_tx, self.q_audio_diar,
            self.q_text, self.q_diarization, self.q_merged,
            self.q_memory, self.q_answer, self.q_rag # q_question is input only usually? but good to close
        ]:
            # q_question might be written to by UI, closing it is fine if we are stopping.
            try:
                q.close()
            except Exception as e:
                logger.error(f"Error closing queue: {e}")
        
        # q_question was missed in the list above
        try:
            self.q_question.close()
        except Exception:
            pass
