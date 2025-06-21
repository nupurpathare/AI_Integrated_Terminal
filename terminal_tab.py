import sys
import os
import pandas as pd
import joblib
import google.generativeai as genai
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabBar, QTabWidget, QWidget, 
    QVBoxLayout, QHBoxLayout, QTextEdit, QListWidget, 
    QListWidgetItem, QLabel, QPushButton, QSplitter, 
    QToolButton, QStyle
)
from PyQt5.QtCore import Qt, QSize, QProcess, QPoint
from PyQt5.QtGui import QTextCursor, QFont, QCursor

class ResizableSuggestionList(QWidget):
    """A resizable suggestion list widget with resize handle."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            background-color: #252525;
            border: 1px solid #333;
            border-radius: 3px;
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with title and close button
        header = QWidget()
        header.setStyleSheet("background-color: #252525;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        self.title_label = QLabel("Suggestions")
        self.title_label.setStyleSheet("color: white; font-size: 12px;")
        
        self.close_btn = QToolButton()
        self.close_btn.setText("×")
        self.close_btn.setStyleSheet("""
            QToolButton {
                color: white; 
                background: transparent;
                border: none;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #333;
            }
        """)
        self.close_btn.clicked.connect(self.hide)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)
        
        # Resize handle (double-headed arrow area)
        self.resize_handle = QWidget()
        self.resize_handle.setFixedHeight(6)
        self.resize_handle.setCursor(QCursor(Qt.SizeVerCursor))
        self.resize_handle.setStyleSheet("""
            background-color: #333;
            border-top: 1px solid #444;
            border-bottom: 1px solid #111;
        """)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #121212;
                color: #D4D4D4;
                font-size: 14px;
                border: none;
            }
            QListWidget::item:selected {
                background-color: #04395E;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #2D2D30;
            }
        """)
        
        layout.addWidget(header)
        layout.addWidget(self.resize_handle)
        layout.addWidget(self.list_widget)
        
        # Resize functionality
        self.drag_start_position = None
        self.original_height = 150
        
        self.resize_handle.mousePressEvent = self.handle_mouse_press
        self.resize_handle.mouseMoveEvent = self.handle_mouse_move
        self.resize_handle.mouseReleaseEvent = self.handle_mouse_release
    
    def handle_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPos()
            self.original_height = self.height()
    
    def handle_mouse_move(self, event):
        if self.drag_start_position is not None:
            delta = event.globalPos() - self.drag_start_position
            new_height = max(100, self.original_height + delta.y())  # Minimum height 100px
            self.resize(self.width(), new_height)
    
    def handle_mouse_release(self, event):
        self.drag_start_position = None
    
    def clear_items(self):
        self.list_widget.clear()
    
    def add_item(self, text):
        item = QListWidgetItem(text)
        self.list_widget.addItem(item)
    
    def set_item_clicked_callback(self, callback):
        self.list_widget.itemClicked.connect(callback)

class TerminalTab(QWidget):
    """A terminal widget with AI integration and command suggestions."""
    def __init__(self):
        super().__init__()
        self.setup_model_and_data()
        self.init_gemini()
        self.init_ui()
        self.init_process()
        self.command_buffer = ""
    
    def setup_model_and_data(self):
        try:
            self.model = joblib.load('rf_model.pkl')
            self.vectorizer = joblib.load('vectorizer.pkl')
            self.commands = pd.read_csv('Commands.csv')
        except Exception as e:
            print(f"Error loading ML model or data: {e}")
            sys.exit(1)
    
    def init_gemini(self):
        genai.configure(api_key="AIzaSyCogCi4lKXJoZ6GTjdz6CKxvsVZKM8jwy0")
        try:
            self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
            print("Gemini model initialized successfully.")
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            sys.exit(1)
    
    def init_process(self):
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyRead.connect(self.read_output)
        shell = "cmd.exe" if sys.platform == "win32" else "bash"
        self.process.start(shell)
        self.write_to_terminal("Welcome to AI-Integrated Terminal!\n")
        self.write_prompt()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("background-color: #121212;")
        main_layout.addWidget(splitter)
        
        # Terminal side
        terminal_container = QWidget()
        terminal_container.setStyleSheet("background-color: #121212;")
        term_layout = QVBoxLayout(terminal_container)
        term_layout.setContentsMargins(0, 0, 0, 0)
        
        self.terminal_display = QTextEdit()
        self.terminal_display.setFont(QFont("Consolas", 11))
        self.terminal_display.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                color: #D4D4D4;
                border: 1px solid #333;
                padding: 5px;
            }
        """)
        self.terminal_display.setReadOnly(False)
        self.terminal_display.setFocus()
        
        # Override events
        self.terminal_display.keyPressEvent = self.handle_key_press
        self.terminal_display.mousePressEvent = self.handle_mouse_press
        
        term_layout.addWidget(self.terminal_display)
        
        # Suggestion list
        self.suggestion_list = ResizableSuggestionList(self)
        self.suggestion_list.set_item_clicked_callback(self.complete_command)
        self.suggestion_list.hide()
        
        # Chat side
        chat_container = QWidget()
        chat_container.setStyleSheet("background-color: #121212;")
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(5, 5, 5, 5)
        
        assistant_label = QLabel(" Ur AI Assistant is here :)")
        assistant_label.setStyleSheet("""
            QLabel {
                color: #D4D4D4;
                font-size: 24px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                color: #D4D4D4;
                border: 1px solid #333;
                border-radius: 3px;
                padding: 8px;
                font-size: 20px;
            }
        """)
        
        self.chat_input = QTextEdit()
        self.chat_input.setFixedHeight(50)
        self.chat_input.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                color: #D4D4D4;
                border: 1px solid #333;
                border-radius: 3px;
                padding: 8px;
                font-size: 20px;
            }
        """)
        self.chat_input.setPlaceholderText("Type your message...")
        
        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #252525;
                color: #D4D4D4;
                border: 1px solid #333;
                border-radius: 3px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        send_button.clicked.connect(self.send_chat_message)
        
        chat_layout.addWidget(assistant_label)
        chat_layout.addWidget(self.chat_display)
        chat_layout.addWidget(self.chat_input)
        chat_layout.addWidget(send_button)
        
        splitter.addWidget(terminal_container)
        splitter.addWidget(chat_container)
        splitter.setSizes([700, 300])
    
    def handle_mouse_press(self, event):
        self.terminal_display.setFocus()
        event.accept()
    
    def handle_key_press(self, event):
        cursor = self.terminal_display.textCursor()
        
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.execute_command()
            cursor.movePosition(QTextCursor.End)
            self.terminal_display.setTextCursor(cursor)
            return
            
        elif event.key() == Qt.Key_Backspace:
            if self.command_buffer:
                self.command_buffer = self.command_buffer[:-1]
                cursor.deletePreviousChar()
        else:
            char = event.text()
            if char.isprintable():
                self.command_buffer += char
                self.terminal_display.insertPlainText(char)
                self.show_suggestions(self.command_buffer)
        
        cursor.movePosition(QTextCursor.End)
        self.terminal_display.setTextCursor(cursor)
    
    def read_output(self):
        output = bytes(self.process.readAllStandardOutput()).decode("utf-8")
        if output.strip():
            if not output.strip().startswith(os.getcwd()):
                self.write_to_terminal(output)
                if not output.endswith('\n'):
                    self.write_to_terminal('\n')
                self.write_prompt()
    
    def write_to_terminal(self, text):
        self.terminal_display.moveCursor(QTextCursor.End)
        self.terminal_display.insertPlainText(text)
        self.terminal_display.moveCursor(QTextCursor.End)
    
    def write_prompt(self):
        current_directory = os.getcwd() if sys.platform == "win32" else "~"
        self.write_to_terminal(f"{current_directory}> ")
        self.command_buffer = ""
    
    def execute_command(self):
        command = self.command_buffer.strip()
        self.write_to_terminal('\n')
        if command:
            self.process.write((command + '\n').encode())
        self.suggestion_list.hide()
    
    def show_suggestions(self, input_text):
        self.suggestion_list.clear_items()
        if input_text:
            try:
                suggestions = [cmd for cmd in self.commands['Command'] if cmd.startswith(input_text)]
                for suggestion in suggestions:
                    self.suggestion_list.add_item(suggestion)
                if suggestions:
                    self.suggestion_list.show()
                    pos = self.terminal_display.mapToGlobal(self.terminal_display.rect().bottomLeft())
                    width = self.terminal_display.width()
                    height = self.suggestion_list.height() if self.suggestion_list.isVisible() else 150
                    self.suggestion_list.setGeometry(pos.x(), pos.y() - height, width, height)
                else:
                    self.suggestion_list.hide()
            except Exception as e:
                print(f"Error fetching suggestions: {e}")
        else:
            self.suggestion_list.hide()
    
    def complete_command(self, item):
        completed_command = item.text()
        cursor = self.terminal_display.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
        cursor.insertText(f"{os.getcwd() if sys.platform == 'win32' else '~'}> {completed_command}")
        self.command_buffer = completed_command
        self.suggestion_list.hide()
        self.terminal_display.setFocus()
    
    def send_chat_message(self):
        user_message = self.chat_input.toPlainText().strip()
        if user_message:
            self.chat_display.append(f"You: {user_message}")
            self.chat_input.clear()
            response = self.send_message_to_gemini(user_message)
            self.chat_display.append(f"AI: {response}\n")
    
    def send_message_to_gemini(self, message):
        try:
            response = self.gemini_model.generate_content(message)
            return response.text
        except Exception as e:
            print(f"Error communicating with Gemini: {e}")
            return "Sorry, I couldn't process your request."
    
    def closeEvent(self, event):
        if self.process.state() == QProcess.Running:
            self.process.terminate()
            self.process.waitForFinished()
        event.accept()

class CustomTabBar(QTabBar):
    def __init__(self):
        super().__init__()
        self.setMovable(True)
        self.setStyleSheet("""
            QTabBar {
                background-color: #252525;
                border: none;
            }
            QTabBar::tab {
                background-color: #252525;
                color: #D4D4D4;
                padding: 8px;
                border: 1px solid #333;
                border-bottom: none;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #121212;
                border-bottom: 1px solid #121212;
            }
            QTabBar::tab:hover {
                background-color: #333;
            }
        """)
        
    def tabSizeHint(self, index):
        if index == self.count() - 1:
            return QSize(50, 30)
        return QSize(150, 30)

class CustomTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setTabBar(CustomTabBar())
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333;
                border-top: none;
                background-color: #121212;
            }
        """)
        
        self.plus_tab = QWidget()
        self.addTab(self.plus_tab, "+")
        self.tabBar().tabButton(self.count()-1, QTabBar.RightSide).resize(0, 0)
        self.tabBar().tabBarClicked.connect(self.handle_tab_click)
        
        self.add_new_terminal_tab()
    
    def add_new_terminal_tab(self):
        terminal_tab = TerminalTab()
        index = self.count() - 1
        self.insertTab(index, terminal_tab, f"Terminal {index + 1}")
        self.setCurrentIndex(index)
    
    def close_tab(self, index):
        if self.widget(index) == self.plus_tab:
            return
        widget = self.widget(index)
        widget.deleteLater()
        self.removeTab(index)
    
    def handle_tab_click(self, index):
        if self.widget(index) == self.plus_tab:
            self.add_new_terminal_tab()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Velocity Terminal")
        self.resize(1200, 700)
        
        # Remove default title bar
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title bar container
        title_bar = QWidget()
        title_bar.setStyleSheet("background-color: #252525;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget
        self.tab_widget = CustomTabWidget()
        title_layout.addWidget(self.tab_widget.tabBar())
        
        # Spacer
        title_layout.addStretch()
        
        # Window controls
        self.minimize_btn = QPushButton()
        self.minimize_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMinButton))
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: white;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        self.minimize_btn.clicked.connect(self.showMinimized)
        
        self.maximize_btn = QPushButton()
        self.maximize_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        self.maximize_btn.setFixedSize(30, 30)
        self.maximize_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: white;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        
        self.close_btn = QPushButton()
        self.close_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: white;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(self.minimize_btn)
        title_layout.addWidget(self.maximize_btn)
        title_layout.addWidget(self.close_btn)
        
        layout.addWidget(title_bar)
        layout.addWidget(self.tab_widget)
        
        # Window dragging
        self.drag_start_position = None
        title_bar.mousePressEvent = self.title_mouse_press
        title_bar.mouseMoveEvent = self.title_mouse_move
        title_bar.mouseReleaseEvent = self.title_mouse_release
    
    def title_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPos()
    
    def title_mouse_move(self, event):
        if self.drag_start_position is not None:
            self.move(self.pos() + (event.globalPos() - self.drag_start_position))
            self.drag_start_position = event.globalPos()
    
    def title_mouse_release(self, event):
        self.drag_start_position = None
    
    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Dark palette
    palette = app.palette()
    palette.setColor(palette.Window, QColor(18, 18, 18))
    palette.setColor(palette.WindowText, Qt.white)
    palette.setColor(palette.Base, QColor(25, 25, 25))
    palette.setColor(palette.Text, Qt.white)
    palette.setColor(palette.Button, QColor(53, 53, 53))
    palette.setColor(palette.ButtonText, Qt.white)
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())