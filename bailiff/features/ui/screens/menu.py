from bailiff.features.audio_ingest.capture import AudioCaptureManager
from bailiff.features.ui.screens.execution import ExecutionScreen
from bailiff.features.ui.screens.list_meetings import ListMeetingsScreen
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Button, Static, Label
from textual.containers import Container, Vertical, Horizontal
from textual import work

# Define the art here
ASCII_TITLE = """\
 ▄▄▄▄    ▄▄▄        ██▓ ██▓      ██▓  █████▒ █████▒
▓█████▄ ▒████▄    ▓██▒▓██▒     ▓██▒▓██   ▒▓██   ▒ 
▒██▒ ▄██▒██  ▀█▄  ▒██▒▒██░     ▒██▒▒████ ░▒████ ░ 
▒██░█▀  ░██▄▄▄▄██ ░██░▒██░     ░██░░▓█▒  ░░▓█▒  ░ 
░▓█  ▀█▓ ▓█   ▓██▒░██░░██████▒░██░░▒█░   ░▒█░     
░▒▓███▀▒ ▒▒   ▓▒█░░▓  ░ ▒░▓  ░░▓   ▒ ░    ▒ ░     
 ▒░▒   ░   ▒   ▒▒ ░ ▒ ░░ ░ ▒  ░ ▒ ░ ░      ░      
  ░    ░   ░   ▒    ▒ ░  ░ ░    ▒ ░ ░ ░    ░ ░    
  ░            ░  ░ ░      ░  ░ ░                 
                                                  """

class MenuScreen(Screen):
    """
    The main menu screen of the application.

    Provides navigation to start new meetings, list past meetings, or exit the app.
    Also performs initial system checks for audio devices (microphone and loopback).
    """
    CSS = """
    MenuScreen {
        align: center middle;
    }

    #title {
        align: center middle;
        padding: 1 2 0 2;
        width: 100%;
        height: auto;
        margin-bottom: 0;
    }
    
    .title-text {
        width: auto;
        color: $accent;
    }

    #status-area {
        layout: horizontal;
        align: center middle;
        height: auto;
        margin-bottom: 0; 
        width: 100%;
    }

    .status-item {
        margin: 0 1;        /* Reduced margin between items */
        padding: 0 1;       /* Reduced internal padding */
        border: solid $secondary;
        width: 22;          /* SIGNIFICANTLY SMALLER (was 30) */
        height: 3;          /* SIGNIFICANTLY SMALLER (was 5) */
        text-align: center;
        content-align: center middle; /* Ensures text is centered in smaller box */
    }
    
    .status-good {
        border: solid $success;
        border-title-color: $success;
        color: $success;
    }
    
    .status-bad {
        border: solid $error;
        border-title-color: $error;
        color: $error;
    }

    #buttons-area {
        layout: horizontal;
        align: center middle;
        height: auto;
        width: 100%;
    }

    Button {
        margin: 0 1;   /* Reduced margin between buttons */
        min-width: 10; /* Ensures very short words aren't too thin */
        width: auto;   /* Let button fit the text */
        height: 1;     /* SMALLEST HEIGHT (was 3) */
        border: none;  /* Optional: removes border to make it even cleaner */
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="main-container"):
            # Title
            with Vertical(id="title"):
                # Use Static instead of Label for ASCII blocks
                yield Static(ASCII_TITLE, classes="title-text")

            # Status Area
            with Horizontal(id="status-area"):
                yield Label("Speaker Status: Checking...", id="status-speaker", classes="status-item")
                yield Label("Mic Status: Checking...", id="status-mic", classes="status-item")

            # Buttons Area
            with Horizontal(id="buttons-area"):
                yield Button("New Meeting", id="btn-new", variant="primary")
                yield Button("List Meetings", id="btn-list")
                yield Button("Settings", id="btn-settings", disabled=True)
                yield Button("Exit", id="btn-exit", variant="error")

        yield Footer()

    def on_mount(self) -> None:
        self.check_devices()

    @work(thread=True)
    def check_devices(self) -> None:
        """
        Check for audio devices in a background thread to avoid blocking UI.
        """
        try:
            mgr = AudioCaptureManager()
            
            # Check mic
            try:
                mic_index = mgr.get_default_microphone()
                mic_ok = True
            except Exception:
                mic_ok = False
            
            # Check loopback
            loopback_info = mgr.get_system_loopback()
            speaker_ok = loopback_info is not None
            
            mgr.terminate()
            
            # Update UI
            self.app.call_from_thread(self.update_status, speaker_ok, mic_ok)
            
        except Exception as e:
            # Fallback if specific check fails
             self.app.call_from_thread(self.update_status, False, False)

    def update_status(self, speaker_ok: bool, mic_ok: bool) -> None:
        speaker_lbl = self.query_one("#status-speaker", Label)
        mic_lbl = self.query_one("#status-mic", Label)

        if speaker_ok:
            speaker_lbl.update("Speaker Status: 🟢")
            speaker_lbl.add_class("status-good")
        else:
            speaker_lbl.update("Speaker Status: 🔴")
            speaker_lbl.add_class("status-bad")

        if mic_ok:
            mic_lbl.update("Mic Status: 🟢")
            mic_lbl.add_class("status-good")
        else:
            mic_lbl.update("Mic Status: 🔴")
            mic_lbl.add_class("status-bad")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new":
            self.app.push_screen(ExecutionScreen())
        elif event.button.id == "btn-list":
            self.app.push_screen(ListMeetingsScreen())
        elif event.button.id == "btn-exit":
            self.app.exit()
