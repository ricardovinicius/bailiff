from multiprocessing.queues import Queue as ProcessQueue
import logging
from typing import Callable
from bailiff.features.memory.storage import MeetingStorage
from bailiff.features.memory.vector_db import VectorMemory
from bailiff.core.db import SessionLocal
from bailiff.core.events import SearchRequest, TranscriptionSegment

logger = logging.getLogger("bailiff.memory.service")

class MemoryService:
    def __init__(self, input_queue: ProcessQueue, session_id: int):
        self.input_queue = input_queue
        self.session_id = session_id
        self.current_session = None
        self.sql_db = None
        self.vector_db = None
    
    def run(self):
        # Initialize resources in the process
        db_session = SessionLocal()
        self.sql_db = MeetingStorage(db=db_session)
        self.vector_db = VectorMemory()

        try:
            # Load existing session
            self.current_session = self.sql_db.get_session(self.session_id)
            if not self.current_session:
                logger.error(f"Session {self.session_id} not found!")
                return
                
            logger.info(f"Memory Service started for session: {self.current_session.name}")

            while True:
                try:
                    item = self.input_queue.get(timeout=0.1)
                    if item is None:
                        logger.info("Received stop signal. Shutting down Memory Service.")
                        break
                    
                    if isinstance(item, TranscriptionSegment):
                        self.vector_db.add_segment(str(self.current_session.id), item)
                        self.sql_db.save_transcript(self.current_session.id, item)
                    elif isinstance(item, SearchRequest):
                        results = self.vector_db.search(item.query, item.session_id, item.k)
                        item.reply_queue.put(results)
                    else:
                        logger.warning(f"Unknown item type received in MemoryService: {type(item)}")

                except Exception as e:
                    # Queue.Empty is raised by get(timeout=...) if no item is available, 
                    # but since we import the queue class but not the exception, 
                    # we need to be careful. However, pure multiprocessing.Queue.get 
                    # raises queue.Empty. 
                    # For simplicty with the type hint, we catch generic Exception but 
                    # practically we should import Empty. 
                    # Actually, let's just use a blocking get with a Sentinel.
                    import queue
                    if isinstance(e, queue.Empty):
                        continue
                        
                    logger.error("Error saving transcription to memory: %s", e)
                    continue
        finally:
            if self.sql_db and self.sql_db.db:
                self.sql_db.db.close()

def run_memory_service(input_queue: ProcessQueue, session_id: int):
    service = MemoryService(input_queue=input_queue, session_id=session_id)
    service.run()