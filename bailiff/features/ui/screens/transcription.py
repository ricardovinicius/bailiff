from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Label, Button
from textual.containers import Container, VerticalScroll, Horizontal

from bailiff.core.events import TranscriptionSegment
from bailiff.core.db import SessionLocal
from bailiff.features.memory.storage import MeetingStorage
from bailiff.features.ui.widgets import TranscriptItem
from bailiff.features.analysis.exporter import Exporter

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
        margin-bottom: 1;
    }

    #buttons-container {
        height: auto;
        dock: bottom;
        align: center middle;
        padding: 1;
    }

    Button {
        height: 1;
        min-width: 10;
        border: none;
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
            with VerticalScroll(id="transcript-scroll"):
                pass # Items will be mounted here
            
            with Container(id="buttons-container"):
                 yield Button("Export", id="btn-export", variant="success")

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-export":
            self.export_transcript()

    def export_transcript(self) -> None:
        try:
            with SessionLocal() as db:
                storage = MeetingStorage(db=db)
                exporter = Exporter(self.session_id, "exports", storage)
                filename = exporter.raw_export()
                self.notify(f"Exported to {filename}", title="Success", severity="information")
        except Exception as e:
            self.notify(f"Export failed: {str(e)}", title="Error", severity="error")

