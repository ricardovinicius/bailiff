from pydantic import BaseModel, Field

class MeetingRealTimeQAResponse(BaseModel):
    answer: str = Field(description="The answer to the question")
    sources: list[str] = Field(description="The sources used to answer the question")
    confidence: float = Field(description="The confidence level of the answer")