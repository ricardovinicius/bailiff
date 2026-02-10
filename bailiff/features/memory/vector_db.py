from bailiff.core.events import TranscriptionSegment
import chromadb
from chromadb.utils import embedding_functions 

class VectorMemory:
    def __init__(self, persist_path: str = "./chromadb"):
        self.client = chromadb.PersistentClient(persist_path)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        # We use a single collection and filter by session_id in metadata when needed
        self.collection = self.client.get_or_create_collection(
            name="meeting_context", 
            embedding_function=self.embedding_fn
        )
    
    def add_segment(self, session_id: str, segment: TranscriptionSegment):
        """
        Embeds and stores the given transcription segment in the vector database.
        """
        doc_id = f"{session_id}_{segment.start_time:.2f}"

        self.collection.add(
            documents=[segment.text],
            metadatas=[{"session_id": session_id, "speaker": segment.speaker, "start_time": segment.start_time, "end_time": segment.end_time}],
            ids=[doc_id]
        )

        return doc_id
    
    def search(self, query: str, session_id: str | None = None, k: int = 5) -> list[str]:
        """
        Searches for the most similar documents to the given query.
        """
        where = {"session_id": session_id} if session_id else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where
        )

        return results['documents'][0]
    

        