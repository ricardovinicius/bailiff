from rich.text import Text
from textual.widgets import Static

from bailiff.core.events import TranscriptionSegment


class TranscriptItem(Static):
    """
    A widget representing a single item in the transcript view.

    Can display either a transcription segment (with timestamps and speaker) or a Q&A exchange.
    """
    def __init__(self, content: TranscriptionSegment | str, role: str = "user", **kwargs):
        if isinstance(content, TranscriptionSegment):
            self.segment = content
            self.text_content = content.text
            self.role = "user" # default for segments
        else:
            self.segment = None
            self.text_content = content
            self.role = role
            
        super().__init__(**kwargs)
    
    def render(self) -> Text:
        if self.segment:
           return Text.assemble(
               (f"[{self.segment.start_time:.1f}s - {self.segment.end_time:.1f}s] ", "dim"),
               (f"[{self.segment.speaker}] ", "bold magenta"),
               self.text_content,
           )
        else:
            # Format for Q&A
            prefix = "[You] " if self.role == "user" else "[Assistant] "
            color = "green" if self.role == "user" else "blue"
            return Text.assemble(
                (prefix, f"bold {color}"),
                self.text_content
            )