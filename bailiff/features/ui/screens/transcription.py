from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Label, Button
from textual.containers import Container, VerticalScroll, Horizontal

from bailiff.core.events import TranscriptionSegment
from bailiff.core.db import SessionLocal
from bailiff.features.memory.storage import MeetingStorage
from bailiff.features.ui.widgets import TranscriptItem
from bailiff.features.analysis.exporter import Exporter
from bailiff.features.assistant.llm import LLMClient, LLMClientSettings
from bailiff.features.analysis.digestion import Digester

from bailiff.features.analysis.summarization import Summarizer

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
        margin: 0 1; 
    }
    """

    def __init__(self, session_id: int):
        super().__init__()
        self.session_id = session_id
        self.session_name = "Unknown Session"

    # FIXME: If leave the transcription of a finished session, it get back to the execution screen instead of the session list screen
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="transcript-container"):
            yield Label("Loading...", id="session-title")
            with VerticalScroll(id="transcript-scroll"):
                pass # Items will be mounted here
            
            with Horizontal(id="buttons-container"):
                yield Button("Export Raw", id="btn-export", variant="primary")
                yield Button("Digest", id="btn-digest", variant="success")
                yield Button("Summary", id="btn-summary", variant="warning")
                yield Button("Full Export", id="btn-full", variant="error")

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
        elif event.button.id == "btn-digest":
            self.process_export("digest")
        elif event.button.id == "btn-summary":
            self.process_export("summary")
        elif event.button.id == "btn-full":
            self.process_export("full")

    def export_transcript(self) -> None:
        try:
            with SessionLocal() as db:
                storage = MeetingStorage(db=db)
                # Exporter init signature: session_id, output_path, storage, digester=None, summarizer=None
                exporter = Exporter(self.session_id, "exports", storage)
                filename = exporter.raw_export()
                self.notify(f"Exported to {filename}", title="Success", severity="information")
        except Exception as e:
            self.notify(f"Export failed: {str(e)}", title="Error", severity="error")

    def process_export(self, mode: str) -> None:
        self.notify(f"Starting {mode} export... this may take a while.", title="Processing", severity="warning")
        # Run in a worker to avoid blocking the UI
        self.run_worker(lambda: self._export_worker(mode), thread=True)

    def _export_worker(self, mode: str):
        try:
            from bailiff.core.config import settings
            
            api_key = settings.models.llm_api_key.get_secret_value() if settings.models.llm_api_key else None
            base_url = settings.models.llm_base_url
            
            model_digestion = settings.models.llm_digestion
            model_summary = settings.models.llm_summary

            with SessionLocal() as db:
                storage = MeetingStorage(db=db)
                
                # Digester LLM
                settings_digestion = LLMClientSettings(api_key=api_key, base_url=base_url, model=model_digestion)
                llm_digestion = LLMClient(settings=settings_digestion)
                digester = Digester(storage, llm_digestion)
                
                # Summarizer LLM
                settings_summary = LLMClientSettings(api_key=api_key, base_url=base_url, model=model_summary)
                llm_summary = LLMClient(settings=settings_summary)
                summarizer = Summarizer(llm_summary)
                
                exporter = Exporter(self.session_id, "exports", storage, digester, summarizer)
                
                if mode == "digest":
                    result = exporter.digest_export()
                    msg = f"Digest exported to {result}"
                elif mode == "summary":
                    result = exporter.summary_export()
                    msg = f"Summary exported to {result}"
                elif mode == "full":
                    raw, digest, summary = exporter.full_export()
                    msg = f"Full export complete.\nRaw: {raw}\nDigest: {digest}\nSummary: {summary}"
                else:
                    raise ValueError(f"Unknown export mode: {mode}")
                
                self.app.call_from_thread(
                    self.notify, 
                    msg, 
                    title="Success", 
                    severity="information"
                )
        except Exception as e:
            self.app.call_from_thread(
                self.notify, 
                f"{mode.capitalize()} failed: {str(e)}", 
                title="Error", 
                severity="error"
            )

