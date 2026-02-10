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
        session_id: int
    ):
        self.question_queue = question_queue
        self.answer_queue = answer_queue
        self.memory_queue = memory_queue
        self.rag_engine = None
        self.llm = None
        self.vector_db = None
        self.session_id = str(session_id) 
    
    def run(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY") # TODO: Move this to a config file
        base_url = os.getenv("OPENAI_BASE_URL") # TODO: Move this to a config file
        model = os.getenv("OPENAI_MODEL") # TODO: Move this to a config file
        
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables.")
            return

        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables.")
            return

        self.llm = LLMClient(api_key=api_key, base_url=base_url, model=model)
        self.vector_db = VectorMemory()
        self.rag_engine = RagEngine(llm=self.llm, vector_db=self.vector_db)

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

def run_assistant_service(question_queue: ProcessQueue, answer_queue: ProcessQueue, memory_queue: ProcessQueue, session_id: int):
    service = AssistantService(question_queue, answer_queue, memory_queue, session_id)
    service.run()         
        