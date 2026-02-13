from bailiff.features.assistant.llm import LLMClientSettings
from bailiff.core.logging import setup_logging
import logging
import os
from multiprocessing.queues import Queue as ProcessQueue
from dotenv import load_dotenv

from bailiff.features.assistant.rag import RagEngine
from bailiff.features.assistant.llm import LLMClient
from bailiff.features.memory.vector_db import VectorMemory

logger = logging.getLogger("bailiff.assistant.service")

# TODO: I should send recent transcription segments to the LLM to provide context for questions 
# like "what did I just say?" or "what was the last thing I said?"

class AssistantService:
    def __init__(self, 
        question_queue: ProcessQueue,
        answer_queue: ProcessQueue,
        memory_queue: ProcessQueue,
        rag_queue: ProcessQueue,
        session_id: int
    ):
        self.question_queue = question_queue
        self.answer_queue = answer_queue
        self.memory_queue = memory_queue
        self.rag_queue = rag_queue
        self.rag_engine = None
        self.llm = None
        self.vector_db = None
        self.session_id = str(session_id) 
    
    def run(self):
        from bailiff.core.config import settings
        
        api_key = settings.models.llm_api_key.get_secret_value() if settings.models.llm_api_key else None
        base_url = settings.models.llm_base_url
        model = settings.models.llm_assistant
        
        if not api_key and settings.models.llm_provider != "ollama":
            logger.warning("LLM API Key not found in configuration, but might not be needed for local models.")
            # return # Don't return, let it fail downstream if needed or work if it's local

        if not model:
            logger.error("LLM Model not configured.")
            return

        llm_settings = LLMClientSettings(api_key=api_key, base_url=base_url, model=model)

        self.llm = LLMClient(llm_settings)
        self.rag_engine = RagEngine(llm=self.llm, memory_queue=self.memory_queue, rag_queue=self.rag_queue)

        while True:
            try:
                question = self.question_queue.get(timeout=0.1)
                if question is None:
                    break # None is the signal to stop
                
                logger.info(f"Thinking about question: {question}")

                answer = self.rag_engine.answer_question(question, session_id=self.session_id)
                self.answer_queue.put(answer)

            except Exception as e:
                # Handle queue empty if needed, though get(timeout=0.1) raises generic Empty? 
                # multiprocessing.Queue raises queue.Empty. 
                # We should import Empty to be precise, or just catch Exception for now as per previous pattern.
                import queue
                if isinstance(e, queue.Empty):
                    continue
                    
                logger.error("Error answering question: %s", e)
                continue

def run_assistant_service(question_queue: ProcessQueue, answer_queue: ProcessQueue, memory_queue: ProcessQueue, rag_queue: ProcessQueue, session_id: int, log_file: str):
    setup_logging(log_file=log_file)
    service = AssistantService(question_queue, answer_queue, memory_queue, rag_queue, session_id)
    service.run()         
        