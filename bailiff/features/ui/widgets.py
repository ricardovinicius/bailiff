from rich.text import Text
from textual.widgets import Static

from bailiff.core.events import TranscriptionSegment


class TranscriptItem(Static):
    def __init__(self, segment: TranscriptionSegment, **kwargs):
        super().__init__(segment.text, **kwargs)
        self.segment = segment
    
    def render(self) -> Text:
       return Text.assemble(
           (f"[{self.segment.start_time:.1f}s - {self.segment.end_time:.1f}s] ", "dim"),
           self.segment.text,
       )