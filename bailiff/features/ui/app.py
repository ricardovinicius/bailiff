import logging
import multiprocessing
import queue

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Static
from textual.containers import Container, VerticalScroll

from bailiff.features.audio_ingest.service import run_ingest_service
from bailiff.features.transcription.service import run_transcription_service
from bailiff.features.ui.widgets import TranscriptItem
from bailiff.core.config import AudioConfig
from bailiff.core.logging import setup_logging
from bailiff.core.db import get_db
from bailiff.features.memory.storage import MeetingStorage

LOG_FILE = "bailiff.log"

# Configure main-process logging to file so it doesn't corrupt the TUI
setup_logging(log_file=LOG_FILE)
logger = logging.getLogger("bailiff.ui.app")

class BailiffApp(App):
    # TODO: Move this CSS to a separate file
    CSS = """
    Screen {
        layout: grid;
        grid-size: 1 2;
        grid-rows: 1fr auto;
    }
    #transcript-container {
        border: solid green;
        background: $surface;
        height: 100%;
        overflow-y: scroll;
    }
    Input {
        dock: bottom;
    }
    """

    def on_mount(self):
        """
        Initialize Backend and UI
        """
        self.q_audio = multiprocessing.Queue()
        self.q_text = multiprocessing.Queue()

        self.p_ingest = multiprocessing.Process(
            target=run_ingest_service,
            args=(self.q_audio, AudioConfig(), LOG_FILE),
            daemon=True,
            name="audio-ingest",
        )
        self.p_transcribe = multiprocessing.Process(
            target=run_transcription_service,
            args=(self.q_audio, self.q_text, LOG_FILE),
            daemon=True,
            name="transcription",
        )

        self.p_ingest.start()
        self.p_transcribe.start()

        # Database Setup
        self.db_gen = get_db()
        self.db = next(self.db_gen)
        self.storage = MeetingStorage(self.db)
        self.current_session = self.storage.create_session()

        self.run_worker(self.monitor_transcription, exclusive=True, thread=True)
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="transcript-container"):
            yield VerticalScroll(id="transcript")
        yield Input(placeholder="Type something…", id="input")
        yield Footer()

    def monitor_transcription(self):
        """
        Monitor the transcription queue and update the UI.
        Runs in a worker thread — uses call_from_thread to touch the DOM.
        """
        transcript_list = self.query_one("#transcript", VerticalScroll)

        while True:
            try:
                segment = self.q_text.get(timeout=0.1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("Error reading transcription queue: %s", e)
                continue

            if segment is None:
                break

            item = TranscriptItem(segment)
            self.call_from_thread(transcript_list.mount, item)
            self.call_from_thread(item.scroll_visible)
            
    def on_unmount(self):
        """
        Stop the backend processes
        """
        self.p_ingest.terminate()
        self.p_transcribe.terminate()
        self.q_audio.close()
        self.q_text.close()
        
if __name__ == "__main__":
    app = BailiffApp()
    app.run()