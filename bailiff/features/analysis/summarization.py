from bailiff.features.assistant.llm import LLMClient

# TODO: Add support for metadata extraction
# TODO: Add support for export in JSON schema

class Summarizer:
    """
    Generates structured meeting minutes from digested transcripts using an LLM.

    This class constructs prompt to instruct the LLM to extract key information such as
    executive summaries, decisions, action items, and key topics from the meeting text.
    """

    SUMMARIZATION_PROMPT = """
    You are an Elite Executive Assistant specializing in technical and business strategy.
    Your goal is to synthesize meeting transcripts into concise, professional, and actionable Meeting Minutes.

    Strictly follow this Markdown structure:

    # Executive Summary
    (A concise 3-5 line paragraph describing the meeting's objective and primary outcomes. Ideal for a 1-minute read.)

    # Key Decisions
    (List of agreements made. What was approved? What was rejected? Use bullet points.)
    * [Decision 1]
    * [Decision 2]

    # Action Items
    (List of assigned tasks. Who does what, and by when?)
    - [ ] **[Owner]**: [Specific Task] (Due: [Date/Context])
    - [ ] **[Owner]**: [Specific Task]

    # Key Topics
    (Summary of discussions grouped by theme, omitting trivial details.)
    * **[Topic A]**: [Summary of the discussion]
    * **[Topic B]**: [Summary of the discussion]

    # Insights & Notes
    (Noteworthy ideas, risks, or context that are neither tasks nor decisions but are worth recording.)

    ---
    **Golden Rules:**
    1. Be direct and objective. Eliminate small talk and pleasantries.
    2. If a task owner is not clear, mark it as **[TBD]** (To Be Defined).
    3. Infer context where possible, but strictly **DO NOT hallucinate** facts.
    """

    USER_PROMPT = """
    Here is the raw meeting transcript for analysis:

    --- BEGIN TRANSCRIPT ---
    {transcript_text}
    --- END TRANSCRIPT ---

    Generate the Meeting Minutes now.
    """


    def __init__(self, llm: LLMClient):
        self.llm = llm

    def summarize(self, digested_transcript: str) -> str:
        """
        Summarizes the digested transcript.
        """
        messages = [
            {"role": "system", "content": self.SUMMARIZATION_PROMPT},
            {"role": "user", "content": self.USER_PROMPT.format(transcript_text=digested_transcript)}
        ]

        return self.llm.chat(messages)

        
