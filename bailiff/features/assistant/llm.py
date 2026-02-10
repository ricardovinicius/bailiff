import instructor
import openai

# TODO: Add logging

class LLMClient:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o-mini"):
        self.client = instructor.patch(openai.OpenAI(api_key=api_key, base_url=base_url))
        self.model = model
    
    def chat(self, messages: list[dict]) -> str:
        """
        Sends a list of messages to the LLM and returns the response.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content