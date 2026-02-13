from textual.screen import Screen
import logging
import queue

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Button
from textual.containers import Container, VerticalScroll, Horizontal

from bailiff.features.ui.widgets import TranscriptItem
from bailiff.core.logging import setup_logging
from bailiff.core.session import SessionManager
from bailiff.features.ui.screens.transcription import TranscriptionScreen


LOG_FILE = "bailiff.log"

# Configure main-process logging to file so it doesn't corrupt the TUI
setup_logging(log_file=LOG_FILE)
logger = logging.getLogger("bailiff.ui.screens.execution")

class ExecutionScreen(Screen):
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
    
    #input-container {
        dock: bottom;
        height: auto;
        padding: 1;
    }

    Input {
        width: 80%;
    }

    Button {
        width: 20%;
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="transcript-container"):
            yield VerticalScroll(id="transcript")
        
        with Horizontal(id="input-container"):
            yield Input(placeholder="Type something…", id="input")
            yield Button("End Meeting", id="btn-end", variant="error")
            
        yield Footer()

    def on_mount(self):
        """
        Initialize Backend and UI
        """
        self.session_manager = SessionManager(log_file=LOG_FILE)
        self.session_manager.start()

        self.run_worker(self.monitor_transcription, thread=True)
        self.run_worker(self.monitor_answers, thread=True)

    def monitor_transcription(self):
        """
        Monitor the merged (transcription + diarization) queue and update the UI.
        Runs in a worker thread — uses call_from_thread to touch the DOM.
        """
        logger.info("Starting transcription monitor")
        transcript_list = self.query_one("#transcript", VerticalScroll)

        while True:
            try:
                if not hasattr(self, 'session_manager'):
                    break
                segment = self.session_manager.q_merged.get(timeout=0.1)
                logger.info(f"Received segment: {segment}")
            except queue.Empty:
                continue
            except Exception as e:
                # logger.error("Error reading merged queue: %s", e)
                continue

            if segment is None:
                break

            # Forward to memory service
            try:
                self.session_manager.q_memory.put(segment)
            except Exception as e:
                logger.error("Error forwarding to memory queue: %s", e)

            item = TranscriptItem(segment)
            self.app.call_from_thread(transcript_list.mount, item)
            self.app.call_from_thread(item.scroll_visible)

    def monitor_answers(self):
        """
        Monitor the answer queue and update the UI.
        Runs in a worker thread — uses call_from_thread to touch the DOM.
        """
        logger.info("Starting answer monitor")
        transcript_list = self.query_one("#transcript", VerticalScroll)

        while True:
            try:
                if not hasattr(self, 'session_manager'):
                    break
                answer = self.session_manager.q_answer.get(timeout=0.1)
            except queue.Empty:
                continue
            except Exception as e:
                # logger.error("Error reading answer queue: %s", e)
                continue

            if answer is None:
                break
            
            logger.info(f"Received answer: {answer}")
            item = TranscriptItem(answer, role="assistant")
            self.app.call_from_thread(transcript_list.mount, item)
            self.app.call_from_thread(item.scroll_visible)
    
    def on_input_submitted(self, event: Input.Submitted):
        """
        Handle user input.
        """
        question = event.value
        if not question:
            return
        
        self.session_manager.q_question.put(question)
        self.query_one("#input").value = ""

        # Display user question in transcript
        transcript_list = self.query_one("#transcript", VerticalScroll)
        item = TranscriptItem(question, role="user")
        transcript_list.mount(item)
        item.scroll_visible()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-end":
            self.stop_meeting()

    def stop_meeting(self):
        session_id = self.session_manager.session_id
        self.session_manager.stop()
        del self.session_manager
        
        # Navigate to transcription screen
        self.app.push_screen(TranscriptionScreen(session_id))

    def on_unmount(self):
        """
        Stop the backend processes
        """
        if hasattr(self, 'session_manager'):
            self.session_manager.stop()
