from collections import deque
import logging
from bailiff.core.events import TranscriptionSegment
import chromadb
from chromadb.utils import embedding_functions 

logger = logging.getLogger("bailiff.memory.vector_db")

# TODO: Improve the search, to avoid duplication of context, giving more variability.

class VectorMemory:
    """
    Manages semantic storage and retrieval using ChromaDB.
    
    Handles embedding and storage of transcript segments for vector-based similarity search.
    Maintains a rolling context window to cluster short segments before embedding.
    """
    MAX_SEGMENT_LENGTH = 500  # max characters per segment in the context window

    def __init__(self, persist_path: str = "./chromadb"):
        self.client = chromadb.PersistentClient(persist_path)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        # We use a single collection and filter by session_id in metadata when needed
        self.collection = self.client.get_or_create_collection(
            name="meeting_context", 
            embedding_function=self.embedding_fn
        )

        self.context_window = deque(maxlen=10)
        self.last_session_id = None
    
    def add_segment(self, session_id: str, segment: TranscriptionSegment):
        """
        Embeds and stores the given transcription segment in the vector database.
        """
        if self.last_session_id != session_id:
            self.context_window.clear()
            self.last_session_id = session_id

        truncated_text = segment.text[:self.MAX_SEGMENT_LENGTH]
        self.context_window.append(truncated_text)
        context_text = "\n".join(self.context_window)

        timestamp_ms = int(segment.start_time * 1000)
        doc_id = f"{session_id}_{timestamp_ms}"

        logger.info(f"Adding segment '{segment.text}' to session '{session_id}'")

        self.collection.upsert(
            documents=[context_text],
            metadatas=[{"session_id": session_id, "speaker": segment.speaker, "start_time": segment.start_time, "end_time": segment.end_time}],
            ids=[doc_id]
        )

        logger.info(f"Added segment '{segment.text}' to session '{session_id}' with ID '{doc_id}'")

        return doc_id
    
    def search(self, query: str, session_id: str | None = None, k: int = 5) -> list[str]:
        """
        Searches for the most similar documents to the given query.
        """
        logger.info(f"Searching for '{query}' in session '{session_id}'")

        where = {"session_id": session_id} if session_id else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where
        )

        logger.info(f"Found {len(results['documents'][0])} results")

        return results['documents'][0]
    

        