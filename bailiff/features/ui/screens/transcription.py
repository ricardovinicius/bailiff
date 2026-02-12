from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Label
from textual.containers import Container, VerticalScroll

from bailiff.core.events import TranscriptionSegment
from bailiff.core.db import SessionLocal
from bailiff.features.memory.storage import MeetingStorage
from bailiff.features.ui.widgets import TranscriptItem

class TranscriptionScreen(Screen):
    CSS = """
    TranscriptionScreen {
        align: center middle;
    }

    #transcript-container {
        border: solid $accent;
        background: $surface;
        height: 100%;
        width: 100%;
    }

    #session-title {
        text-align: center;
        width: 100%;
        padding: 1;
        background: $secondary;
        color: $text;
        dock: top;
    }
    
    VerticalScroll {
        height: 1fr;
        width: 100%;
        overflow-y: scroll;
    }
    """

    def __init__(self, session_id: int):
        super().__init__()
        self.session_id = session_id
        self.session_name = "Unknown Session"

    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="transcript-container"):
            yield Label("Loading...", id="session-title")
            yield VerticalScroll(id="transcript-scroll")
        yield Footer()

    def on_mount(self) -> None:
        scroll_view = self.query_one("#transcript-scroll", VerticalScroll)
        
        # Load transcript
        with SessionLocal() as db:
            storage = MeetingStorage(db=db)
            
            # Get Session Details
            session = storage.get_session(self.session_id)
            if session:
                self.session_name = session.name
                self.query_one("#session-title").update(f"Transcript: {session.name}")
            
            # Get Transcripts
            transcripts = storage.get_transcripts(self.session_id)
            
            for t in transcripts:
                # Create TranscriptionSegment for compatibility with TranscriptItem
                segment = TranscriptionSegment(
                    text=t.text,
                    start_time=t.start_time,
                    end_time=t.end_time,
                    duration=t.end_time - t.start_time,
                    speaker=t.speaker
                )
                item = TranscriptItem(segment)
                scroll_view.mount(item)

