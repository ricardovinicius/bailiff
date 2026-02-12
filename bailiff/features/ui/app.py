from bailiff.features.assistant.service import run_assistant_service
import logging
import multiprocessing
import queue
import threading

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Static
from textual.containers import Container, VerticalScroll

from bailiff.features.audio_ingest.service import run_ingest_service
from bailiff.features.transcription.service import run_transcription_service
from bailiff.features.diarization.service import run_diarization_service
from bailiff.features.diarization.merge import run_merge_service
from bailiff.features.memory.service import run_memory_service
from bailiff.features.ui.widgets import TranscriptItem
from bailiff.features.memory.storage import MeetingStorage
from bailiff.core.db import SessionLocal
from bailiff.core.config import AudioConfig
from bailiff.core.logging import setup_logging
from bailiff.core.db import get_db

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
        # Audio fan-out: ingest → raw → [transcription, diarization]
        self.q_audio_raw = multiprocessing.Queue()    # ingest output
        self.q_audio_tx = multiprocessing.Queue()     # copy for transcription
        self.q_audio_diar = multiprocessing.Queue()   # copy for diarization

        self.q_text = multiprocessing.Queue()          # transcription output
        self.q_diarization = multiprocessing.Queue()   # diarization output
        self.q_merged = multiprocessing.Queue()        # merge output → UI

        self.q_memory = multiprocessing.Queue()
        self.q_question = multiprocessing.Queue()
        self.q_answer = multiprocessing.Queue()
        self.q_rag = multiprocessing.Queue()

        # Create session
        db = SessionLocal()
        storage = MeetingStorage(db)
        session = storage.create_session()
        self.session_id = session.id
        db.close()

        # Fan-out thread: duplicates audio chunks to transcription + diarization
        self._fanout_stop = threading.Event()
        self._fanout_thread = threading.Thread(
            target=self._audio_fanout, daemon=True, name="audio-fanout"
        )
        self._fanout_thread.start()

        self.p_ingest = multiprocessing.Process(
            target=run_ingest_service,
            args=(self.q_audio_raw, AudioConfig(), LOG_FILE),
            daemon=True,
            name="audio-ingest",
        )
        self.p_transcribe = multiprocessing.Process(
            target=run_transcription_service,
            args=(self.q_audio_tx, self.q_text, LOG_FILE),
            daemon=True,
            name="transcription",
        )
        self.p_diarize = multiprocessing.Process(
            target=run_diarization_service,
            args=(self.q_audio_diar, self.q_diarization, LOG_FILE),
            daemon=True,
            name="diarization",
        )
        self.p_merge = multiprocessing.Process(
            target=run_merge_service,
            args=(self.q_text, self.q_diarization, self.q_merged, LOG_FILE),
            daemon=True,
            name="merge",
        )
        self.p_memory = multiprocessing.Process(
            target=run_memory_service,
            args=(self.q_memory, self.q_rag, self.session_id, LOG_FILE),
            daemon=True,
            name="memory",
        )
        self.p_assistant = multiprocessing.Process(
            target=run_assistant_service,
            args=(self.q_question, self.q_answer, self.q_memory, self.q_rag, self.session_id, LOG_FILE),
            daemon=True,
            name="assistant",
        )

        self.p_ingest.start()
        self.p_transcribe.start()
        self.p_diarize.start()
        self.p_merge.start()
        self.p_memory.start()
        self.p_assistant.start()

        self.run_worker(self.monitor_transcription, exclusive=True, thread=True)
        self.run_worker(self.monitor_answers, exclusive=True, thread=True)
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="transcript-container"):
            yield VerticalScroll(id="transcript")
        yield Input(placeholder="Type something…", id="input")
        yield Footer()

    def _audio_fanout(self):
        """
        Duplicate audio chunks from ingest to both transcription and diarization queues.
        """
        while not self._fanout_stop.is_set():
            try:
                chunk = self.q_audio_raw.get(timeout=0.5)
            except queue.Empty:
                continue
            self.q_audio_tx.put(chunk)
            self.q_audio_diar.put(chunk)
            if chunk is None:
                break  # poison pill forwarded to both consumers

    def monitor_transcription(self):
        """
        Monitor the merged (transcription + diarization) queue and update the UI.
        Runs in a worker thread — uses call_from_thread to touch the DOM.
        """
        transcript_list = self.query_one("#transcript", VerticalScroll)

        while True:
            try:
                segment = self.q_merged.get(timeout=0.1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("Error reading merged queue: %s", e)
                continue

            if segment is None:
                break

            # Forward to memory service
            try:
                self.q_memory.put(segment)
            except Exception as e:
                logger.error("Error forwarding to memory queue: %s", e)

            item = TranscriptItem(segment)
            self.call_from_thread(transcript_list.mount, item)
            self.call_from_thread(item.scroll_visible)

    def monitor_answers(self):
        """
        Monitor the answer queue and update the UI.
        Runs in a worker thread — uses call_from_thread to touch the DOM.
        """
        transcript_list = self.query_one("#transcript", VerticalScroll)

        while True:
            try:
                answer = self.q_answer.get(timeout=0.1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("Error reading answer queue: %s", e)
                continue

            if answer is None:
                break
            
            logger.info(f"Received answer: {answer}")
            item = TranscriptItem(answer, role="assistant")
            self.call_from_thread(transcript_list.mount, item)
            self.call_from_thread(item.scroll_visible)
    
    def on_input_submitted(self, event: Input.Submitted):
        """
        Handle user input.
        """
        question = event.value
        if not question:
            return
        
        self.q_question.put(question)
        self.query_one("#input").value = ""

        # Display user question in transcript
        transcript_list = self.query_one("#transcript", VerticalScroll)
        item = TranscriptItem(question, role="user")
        transcript_list.mount(item)
        item.scroll_visible()

    def on_unmount(self):
        """
        Stop the backend processes
        """
        self._fanout_stop.set()
        self.p_ingest.terminate()
        self.p_transcribe.terminate()
        self.p_diarize.terminate()
        self.p_merge.terminate()
        self.p_memory.terminate()
        self.q_audio_raw.close()
        self.q_audio_tx.close()
        self.q_audio_diar.close()
        self.q_text.close()
        self.q_diarization.close()
        self.q_merged.close()
        self.q_memory.close()
        
if __name__ == "__main__":
    app = BailiffApp()
    app.run()