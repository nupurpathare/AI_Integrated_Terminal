import sys
import os
import subprocess

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QHBoxLayout, QFrame, QGridLayout
)
from PyQt5.QtCore import QProcess, Qt, QSize, QPoint
from PyQt5.QtGui import QTextCursor, QFont, QIcon, QPalette, QColor, QFontDatabase
import joblib
import google.generativeai as genai
from PyQt5.QtWidgets import  QLabel, QPushButton, QHBoxLayout
from PyQt5.QtWidgets import QMessageBox
import time
from PyQt5.QtWidgets import QApplication, QMessageBox





class CustomTitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(35)
        self.setup_ui()
        self._dragging = False
        self._startPos = None
        self._windowPos = None

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)

        # Title label
        self.title_label = QLabel("Velocity")
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
        """)

        # New Terminal Button ('+')
        self.new_terminal_btn = QPushButton("+")
        self.new_terminal_btn.setFixedSize(30, 30)
        self.new_terminal_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 18px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.new_terminal_btn.clicked.connect(self.open_new_terminal)

        # Window Control Buttons
        btn_size = 30
        self.minimize_btn = QPushButton("─")
        self.maximize_btn = QPushButton("□")
        self.close_btn = QPushButton("×")

        buttons = [self.minimize_btn, self.maximize_btn, self.close_btn]
        for btn in buttons:
            btn.setFixedSize(btn_size, btn_size)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    font-size: 16px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)

        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #E81123;
                color: white;
            }
        """)

        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.new_terminal_btn)
        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)

        self.setStyleSheet("""
            CustomTitleBar {
                background-color: #2D2D2D;
                border: none;
            }
        """)

        # Connect window control buttons
        self.minimize_btn.clicked.connect(lambda: self.parent.showMinimized())
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.parent.close)

    def toggle_maximize(self):
        """Toggle window between maximized and normal size."""
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, event):
        """Start dragging when mouse is pressed."""
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._startPos = event.globalPos()
            self._windowPos = self.parent.pos()

    def mouseMoveEvent(self, event):
        """Move the window when dragging."""
        if self._dragging:
            delta = event.globalPos() - self._startPos
            self.parent.move(self._windowPos + delta)

    def mouseReleaseEvent(self, event):
        """Stop dragging when mouse is released."""
        if event.button() == Qt.LeftButton:
            self._dragging = False

    def open_new_terminal(self):
        """Open a new instance of the AI terminal in a separate tab."""
        if sys.platform.startswith("win"):
            QProcess.startDetached("wt", ["python", os.path.abspath(__file__), "--new-instance"])
        elif sys.platform.startswith("linux"):
            QProcess.startDetached("gnome-terminal", ["--", "python3", os.path.abspath(__file__), "--new-instance"])
        elif sys.platform.startswith("darwin"):
            QProcess.startDetached("open", ["-n", "-a", "Terminal", os.path.abspath(__file__)])

        print("✅ New AI Terminal instance started as a tab.")
    
class AITerminal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Initialize shell process
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyRead.connect(self.read_output)

        # Start the shell based on platform
        shell = "cmd.exe" if sys.platform == "win32" else "bash"
        self.process.start(shell)

        # Load ML model and vectorizer
        try:
            self.model = joblib.load('rf_model.pkl')
            self.vectorizer = joblib.load('vectorizer.pkl')
            self.commands = pd.read_csv('Commands.csv')
        except Exception as e:
            print(f"Error loading ML model or data: {e}")
            sys.exit(1)

        # Initialize Gemini
        self.init_gemini()

        self.init_ui()
        self.oldPos = self.pos()

    # def open_new_terminal(self):
    #     """Open a new instance of the AI terminal."""
    #     new_process = QProcess()
    #     new_process.start(sys.executable, [__file__])  # Opens another instance of the script
    

    def init_gemini(self):
        """Initialize the Gemini chatbot."""
        genai.configure(api_key='AIzaSyCogCi4lKXJoZ6GTjdz6CKxvsVZKM8jwy0')  # Replace with your actual API key

        # Use the correct model name
        try:
            self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')  # Updated model name
            print("Gemini model initialized successfully.")
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            sys.exit(1)

    def send_message_to_gemini(self, message):
        """Send a message to the Gemini chatbot and get the response."""
        try:
            response = self.gemini_model.generate_content(message)
            return response.text
        except Exception as e:
            print(f"Error communicating with Gemini: {e}")
            return "Sorry, I couldn't process your request."

    def read_output(self):
        """Read and display the output from the process."""
        output = bytes(self.process.readAllStandardOutput()).decode("utf-8")
        if output.strip():
            if not output.strip().startswith(os.getcwd()):
                self.write_to_terminal(output)
                if not output.endswith('\n'):
                    self.write_to_terminal('\n')
                self.write_prompt()

    def write_to_terminal(self, text):
        """Write text to the terminal display."""
        self.terminal_display.moveCursor(QTextCursor.End)
        self.terminal_display.insertPlainText(text)
        self.terminal_display.moveCursor(QTextCursor.End)

    def write_prompt(self):
        """Write the command prompt."""
        current_directory = os.getcwd() if sys.platform == "win32" else "~"
        self.write_to_terminal(f"{current_directory}> ")
        self.command_buffer = ""

    def handle_key_press(self, event):
        """Handle keyboard input in the terminal."""
        key = event.key()
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            self.execute_command()
        elif key == Qt.Key_Backspace:
            if len(self.command_buffer) > 0:
                self.command_buffer = self.command_buffer[:-1]
                cursor = self.terminal_display.textCursor()
                cursor.deletePreviousChar()
        else:
            char = event.text()
            if char.isprintable():
                self.command_buffer += char
                self.terminal_display.insertPlainText(char)
                self.show_suggestions(self.command_buffer)

    def execute_command(self):
        """Execute the current command."""
        command = self.command_buffer.strip()
        self.write_to_terminal('\n')

        if command:
            self.process.write((command + '\n').encode())

        self.suggestion_list.hide()

    def show_suggestions(self, input_text):
        """Show command suggestions based on input."""
        self.suggestion_list.clear()
        if input_text:
            try:
                input_vec = self.vectorizer.transform([input_text])
                prediction = self.model.predict(input_vec)
                suggestions = [cmd for cmd in self.commands['Command'] if cmd.startswith(input_text)]
                for suggestion in suggestions:
                    item = QListWidgetItem(suggestion)
                    self.suggestion_list.addItem(item)
                if suggestions:
                    self.suggestion_list.show()
                    self.suggestion_list.setGeometry(
                        self.terminal_display.geometry().left(),
                        self.terminal_display.geometry().bottom() - 150,
                        self.terminal_display.width(),
                        150
                    )
                else:
                    self.suggestion_list.hide()
            except Exception as e:
                print(f"Error fetching suggestions: {e}")
        else:
            self.suggestion_list.hide()

    def complete_command(self, item):
        """Complete the command with the selected suggestion."""
        completed_command = item.text()
        cursor = self.terminal_display.textCursor()

        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        line_text = cursor.selectedText()

        prompt_text = line_text.split(">")[-1]
        cleaned_prompt = line_text.replace(prompt_text.strip(), "").strip()

        cursor.removeSelectedText()
        cursor.insertText(f"{cleaned_prompt} {completed_command}")
        self.command_buffer = completed_command

        self.terminal_display.setTextCursor(cursor)
        self.suggestion_list.hide()

    def send_chat_message(self):
        """Send the user's message to Gemini and display the response."""
        user_message = self.chat_input.toPlainText().strip()
        if user_message:
            self.chat_display.append(f"You: {user_message}")
            self.chat_input.clear()

            response = self.send_message_to_gemini(user_message)
            self.chat_display.append(f"Gemini: {response}")
            self.chat_display.append("")

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def closeEvent(self, event):
        """Terminate the shell process when the window is closed."""
        if self.process.state() == QProcess.Running:
            self.process.terminate()
            self.process.waitForFinished()
        event.accept()

    def init_ui(self):
        # Main container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Add a button to open a new terminal instance
        # self.new_terminal_button = QPushButton("+")
        # self.new_terminal_button.clicked.connect(self.open_new_terminal)
        # main_layout.addWidget(self.new_terminal_button)


        # Content widget with shadow and rounded corners
        content_widget = QWidget()
        content_widget.setObjectName("ContentWidget")
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(2, 2, 2, 2)

        # Terminal section
        terminal_container = QWidget()
        terminal_layout = QVBoxLayout(terminal_container)
        terminal_layout.setContentsMargins(10, 10, 10, 10)

        # Terminal display with custom font
        self.terminal_display = QTextEdit()
        font = QFont("Consolas", 11)
        self.terminal_display.setFont(font)
        self.terminal_display.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
        """)

        # Suggestion list with modern styling
        self.suggestion_list = QListWidget()
        self.suggestion_list.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #D4D4D4;
                border: 1px solid #3E3E42;
                border-radius: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3E3E42;
            }
            QListWidget::item:selected {
                background-color: #04395E;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #2D2D30;
            }
        """)
        self.suggestion_list.itemClicked.connect(self.complete_command)
        self.suggestion_list.hide()

        # Right panel with gradient background
        right_panel = QWidget()
        right_panel.setFixedWidth(250)
        right_panel.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #1a1a1a, stop:1 #0D0D0D);
                border-radius: 10px;
            }
        """)

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 20, 15, 20)
        right_layout.setSpacing(20)

        # Assistant label with modern design
        assistant_label = QLabel("Ur AI Assistant is Here!")
        assistant_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
        """)

        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)

        # Chat input area
        self.chat_input = QTextEdit()
        self.chat_input.setFixedHeight(50)
        self.chat_input.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        self.chat_input.setPlaceholderText("Type your message here...")

        # Send button
        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0086F0;
            }
            QPushButton:pressed {
                background-color: #006CBC;
            }
        """)
        send_button.clicked.connect(self.send_chat_message)

        # Layout assembly
        terminal_layout.addWidget(self.terminal_display)
        terminal_layout.addWidget(self.suggestion_list)

        right_layout.addWidget(assistant_label)
        right_layout.addWidget(self.chat_display)
        right_layout.addWidget(self.chat_input)
        right_layout.addWidget(send_button)

        content_layout.addWidget(terminal_container, stretch=7)
        content_layout.addWidget(right_panel, stretch=3)

        main_layout.addWidget(content_widget)

        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background: transparent;
            }
            #ContentWidget {
                background-color: #252526;
                border-radius: 10px;
                border: 1px solid #3E3E42;
            }
        """)

        # Connect window control buttons
        self.title_bar.close_btn.clicked.connect(self.close)
        self.title_bar.minimize_btn.clicked.connect(self.showMinimized)
        self.title_bar.maximize_btn.clicked.connect(self.toggle_maximize)

        # Set window size
        self.resize(1200, 700)

        # Initialize terminal
        self.command_buffer = ""
        self.terminal_display.setReadOnly(False)
        self.terminal_display.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.terminal_display.setFocus()
        self.terminal_display.keyPressEvent = self.handle_key_press

        self.write_to_terminal("Welcome to AI-Integrated Terminal!\n")
        self.write_prompt()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    terminal = AITerminal()
    terminal.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()