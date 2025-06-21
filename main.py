import sys
from PyQt5.QtWidgets import (QApplication, QTabWidget, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QMainWindow, QStyle)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor
from terminal_tab import TerminalTab
from PyQt5.QtWidgets import QTabBar, QPushButton

class CustomTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.setExpanding(False)
        self.setStyleSheet("""
            QTabBar {
                background-color: #252525;
                color: #D4D4D4;
                border: none;
            }
            QTabBar::tab {
                background-color: #252525;
                color: #D4D4D4;
                padding: 8px;
                border: 1px solid #333;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #121212;
                border-bottom: 1px solid #121212;
            }
            QTabBar::tab:hover {
                background-color: #333;
            }
            QTabBar::close-button {
                image: none;
                subcontrol-position: right;
                padding: 4px;
            }
            QTabBar::close-button:hover {
                background-color: #ff5555;
                border-radius: 2px;
            }
            QTabBar QToolButton {
                color: white;
                background: transparent;
                border: none;
                font-size: 12px;
            }
            QTabBar QToolButton:hover {
                background-color: #ff5555;
            }
        """)
        
        # Add close buttons to all tabs
        for i in range(self.count()):
            btn = QToolButton(self)
            btn.setText('×')
            btn.setStyleSheet("""
                QToolButton {
                    color: white;
                    background: transparent;
                    border: none;
                    font-size: 12px;
                    padding: 0px;
                    qproperty-icon: none;
                }
                QToolButton:hover {
                    background-color: #ff5555;
                    border-radius: 2px;
                }
            """)
            btn.setFixedSize(16, 16)
            btn.clicked.connect(lambda _, index=i: self.tabCloseRequested.emit(index))
            self.setTabButton(i, QTabBar.RightSide, btn)
        
    def tabSizeHint(self, index):
        if index == self.count() - 1:
            return QSize(50, 30)
        return QSize(150, 30)

# class CustomTabBar(QTabBar):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setMovable(True)
#         self.setExpanding(False)
#         self.setStyleSheet("""
#             QTabBar {
#                 background-color: #252525;
#                 color: #D4D4D4;
#                 border: none;
#             }
#             QTabBar::tab {
#                 background-color: #252525;
#                 color: #D4D4D4;
#                 padding: 8px;
#                 border: 1px solid #333;
#                 border-bottom: none;
#                 border-top-left-radius: 5px;
#                 border-top-right-radius: 5px;
#                 margin-right: 2px;
#             }
#             QTabBar::tab:selected {
#                 background-color: #121212;
#                 border-bottom: 1px solid #121212;
#             }
#             QTabBar::tab:hover {
#                 background-color: #333;
#             }
#             QTabBar::close-button {
#                 subcontrol-position: right;
#                 color: white;
#             }
#         """)
        
#     def tabSizeHint(self, index):
#         if index == self.count() - 1:
#             return QSize(50, 30)
#         return QSize(150, 30)


class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(CustomTabBar(self))
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.setMovable(True)
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
        self.last_selected_index = 0
    
    def add_new_terminal_tab(self):
        terminal_tab = TerminalTab()
        index = self.count() - 1
        self.insertTab(index, terminal_tab, f"🛫 Terminal ")
        self.setCurrentIndex(index)
        self.last_selected_index = index
    
    def close_tab(self, index):
        if self.widget(index) == self.plus_tab:
            return
        widget = self.widget(index)
        widget.deleteLater()
        self.removeTab(index)
        if index == self.last_selected_index:
            self.last_selected_index = max(0, self.currentIndex())
    
    def handle_tab_click(self, index):
        if self.widget(index) == self.plus_tab:
            self.add_new_terminal_tab()
        else:
            self.setCurrentIndex(index)
            self.last_selected_index = index


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Velocity - AI Integrated Terminal")
        self.resize(1200, 700)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #121212;")
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        title_tab_container = QWidget()
        title_tab_container.setStyleSheet("background-color: #252525;")
        title_tab_layout = QHBoxLayout(title_tab_container)
        title_tab_layout.setContentsMargins(0, 0, 0, 0)
        title_tab_layout.setSpacing(0)
        
        self.tab_widget = CustomTabWidget()
        tab_bar = self.tab_widget.tabBar()
        title_tab_layout.addWidget(tab_bar)
        title_tab_layout.addStretch()
        
        # Window buttons
        self.minimize_btn = QPushButton("_")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        self.minimize_btn.clicked.connect(self.showMinimized)
        
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(30, 30)
        self.maximize_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        title_tab_layout.addWidget(self.minimize_btn)
        title_tab_layout.addWidget(self.maximize_btn)
        title_tab_layout.addWidget(self.close_btn)
        
        layout.addWidget(title_tab_container)
        layout.addWidget(self.tab_widget)
        
        self.drag_start_position = None
        title_tab_container.mousePressEvent = self.title_mouse_press
        title_tab_container.mouseMoveEvent = self.title_mouse_move
        title_tab_container.mouseReleaseEvent = self.title_mouse_release
    
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
            self.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    dark_palette = app.palette()
    dark_palette.setColor(dark_palette.Window, QColor(18, 18, 18))
    dark_palette.setColor(dark_palette.WindowText, Qt.white)
    dark_palette.setColor(dark_palette.Base, QColor(25, 25, 25))
    dark_palette.setColor(dark_palette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(dark_palette.ToolTipBase, Qt.white)
    dark_palette.setColor(dark_palette.ToolTipText, Qt.white)
    dark_palette.setColor(dark_palette.Text, Qt.white)
    dark_palette.setColor(dark_palette.Button, QColor(53, 53, 53))
    dark_palette.setColor(dark_palette.ButtonText, Qt.white)
    dark_palette.setColor(dark_palette.BrightText, Qt.red)
    dark_palette.setColor(dark_palette.Link, QColor(42, 130, 218))
    dark_palette.setColor(dark_palette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(dark_palette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)
    
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())