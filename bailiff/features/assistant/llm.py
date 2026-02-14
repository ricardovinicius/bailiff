from bailiff.features.memory.models import Sessions
from bailiff.features.memory.models import Transcripts
import instructor
import openai
import logging

logger = logging.getLogger("bailiff.features.assistant.llm")

class LLMClientSettings:
    """
    Configuration settings for the LLM client.
    """
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

class LLMClient:
    """
    Client for interacting with Large Language Models.

    Wraps the OpenAI client (patched by instructor) to provide a streamlined interface for
    sending messages and receiving completion responses from the configured LLM.
    """
    def __init__(self, settings: LLMClientSettings):
        self.client = instructor.patch(openai.OpenAI(api_key=settings.api_key, base_url=settings.base_url))
        self.model = settings.model
    
    def chat(self, messages: list[dict]) -> str:
        """
        Sends a list of messages to the LLM and returns the response.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3
        ) # TODO: add temperature config to settings
        return response.choices[0].message.content

        
        