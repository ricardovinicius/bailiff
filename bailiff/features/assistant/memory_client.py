import multiprocessing
import logging
from multiprocessing.queues import Queue as ProcessQueue
from bailiff.core.events import SearchRequest

logger = logging.getLogger("bailiff.assistant.memory_client")

class MemoryClient:
    def __init__(self, memory_queue: ProcessQueue):
        self.memory_queue = memory_queue

    def search(self, query: str, session_id: str | None = None, k: int = 5) -> list[str]:
        """
        Sends a search request to the MemoryService and waits for the result.
        """
        # Create a temporary queue via Manager for the response
        # Using a regular Queue inside another Queue fails on Windows
        with multiprocessing.Manager() as manager:
            reply_queue = manager.Queue()
        
        request = SearchRequest(
            query=query,
            session_id=session_id,
            reply_queue=reply_queue,
            k=k
        )
        
        self.memory_queue.put(request)
        
        try:
            # Wait for response with a timeout
            results = reply_queue.get(timeout=10.0)
            return results
        except Exception as e:
            logger.error(f"Error waiting for search results: {e}")
            return []
        finally:
            reply_queue.close()
