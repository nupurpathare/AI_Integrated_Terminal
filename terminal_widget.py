from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class TerminalWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.terminal_display = QTextEdit()
        self.terminal_display.setReadOnly(False)
        self.terminal_display.setStyleSheet("""
            QTextEdit {
                background-color: black;
                color: white;
                font-family: Monospace;
                font-size: 14px;
                border: none;
            }
        """)

        layout.addWidget(self.terminal_display)
