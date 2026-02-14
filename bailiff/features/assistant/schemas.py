from pydantic import BaseModel, Field

class MeetingRealTimeQAResponse(BaseModel):
    """
    Schema for the response to a real-time question during a meeting.
    """
    answer: str = Field(description="The answer to the question")
    sources: list[str] = Field(description="The sources used to answer the question")
    confidence: float = Field(description="The confidence level of the answer")