from multiprocessing.queues import Queue as ProcessQueue
import logging

from bailiff.features.assistant.llm import LLMClient
from bailiff.core.events import SearchRequest

logger = logging.getLogger("bailiff.assistant.rag")

class RagEngine:
    def __init__(self, llm: LLMClient, memory_queue: ProcessQueue, rag_queue: ProcessQueue):
        self.llm = llm
        self.memory_queue = memory_queue
        self.rag_queue = rag_queue
    
    def answer_question(self, question: str, session_id: str | None = None) -> str:
        """
        Answers a question using the RAG engine.
        """
        target_session = session_id

        # Send search request to MemoryService and wait for the reply
        request = SearchRequest(query=question, session_id=target_session)
        self.memory_queue.put(request)

        try:
            results = self.rag_queue.get(timeout=30)
        except Exception:
            logger.error("Timed out waiting for search results from MemoryService")
            return "I'm having trouble searching meeting context right now."
        
        if not results:
            return "I don't have enough information to answer that question."

        context = "\n- ".join(results)
        
        logger.info(f"Answering question '{question}' with context '{context}'")

        system_prompt = f"""
        You are a helpful assistant for a meeting.
        Answer the participant's question based on the context provided below.
        If the answer is not in the context, say "I didn't hear that mentioned."

        --- MEETING CONTEXT ---
        {context}
        """

        return self.llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}"},
        ])