import logging

from bailiff.features.assistant.memory_client import MemoryClient
from bailiff.features.assistant.llm import LLMClient

logger = logging.getLogger("bailiff.assistant.rag")

class RagEngine:
    def __init__(self, memory_client: MemoryClient, llm: LLMClient):
        self.memory_client = memory_client
        self.llm = llm
    
    def answer_question(self, question: str, session_id: str | None = None) -> str:
        """
        Answers a question using the RAG engine.
        """
        results = self.memory_client.search(question, session_id)
        
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