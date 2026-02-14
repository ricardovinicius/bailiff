from textual.app import App

from bailiff.core.config import settings
from bailiff.features.ui.screens.menu import MenuScreen

class BailiffApp(App):
    """
    Main entry point for the Bailiff TUI application.

    Manages the application lifecycle and initial screen loading.
    """
    CSS_PATH = None # or path to global css if valid

    def on_mount(self):
        self.push_screen(MenuScreen())

    def on_unmount(self):
        # Ensure we cleanup if needed, though screens handle their own cleanup
        pass

if __name__ == "__main__":
    app = BailiffApp()
    app.run()