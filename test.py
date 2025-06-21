import sys
import os
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout

class CustomTitleBar:
    def __init__(self, tab_widget):
        self.tab_widget = tab_widget  # Reference to the tab system

    def open_new_terminal(self):
        """Open a new tab in the AI Terminal instead of a system terminal."""
        new_tab = TerminalTab()  # Create a new terminal tab
        self.tab_widget.addTab(new_tab, f"Terminal {self.tab_widget.count() + 1}")
        self.tab_widget.setCurrentWidget(new_tab)  # Switch to the new tab

class TerminalTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.process = QProcess(self)  # Run the terminal process inside this tab
        self.process.setProgram(sys.executable)  # Use the same Python executable
        self.process.setArguments([os.path.abspath(__file__)])  # Relaunch self
        self.process.start()
        layout.addWidget(QWidget())  # Placeholder UI element
        self.setLayout(layout)
