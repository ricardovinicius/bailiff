from bailiff.features.ui.screens.transcription import TranscriptionScreen
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, DataTable, Button
from textual.containers import Container, Vertical

from bailiff.core.db import SessionLocal
from bailiff.features.memory.storage import MeetingStorage

class ListMeetingsScreen(Screen):
    """
    Screen for listing past meeting sessions.

    Fetches session data from the database and displays it in a selectable table.
    Selecting a row navigates to the TranscriptionScreen for that session.
    """
    CSS = """
    ListMeetingsScreen {
        align: center middle;
    }

    #list-container {
        width: 80%;
        height: 80%;
        border: solid $accent;
    }

    DataTable {
        width: 100%;
        height: 1fr;
    }

    #back-btn {
        margin: 1;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="list-container"):
            yield DataTable(cursor_type="row")
            yield Button("Back", id="back-btn", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Name", "Start Time")
        
        # Load sessions
        with SessionLocal() as db:
            storage = MeetingStorage(db=db)
            sessions = storage.get_sessions()
            
            for session in sessions:
                start_time_str = session.start_time.strftime("%Y-%m-%d %H:%M:%S") if session.start_time else "N/A"
                table.add_row(str(session.id), session.name, start_time_str, key=str(session.id))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        session_id = event.row_key.value
        if session_id:
            self.app.push_screen(TranscriptionScreen(session_id=int(session_id)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.app.pop_screen()
