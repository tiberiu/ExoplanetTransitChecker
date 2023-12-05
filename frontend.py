import sys
import threading

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont

import qdarktheme

from widgets.main_widget import MainWidget

class MainWindow(QMainWindow):

    def __init__(self, frontend_thread, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.frontend_thread = frontend_thread
        self.data = None

        self.setWindowTitle("Exoplanet Transit")

        self.setFixedWidth(1920)
        self.setFixedHeight(1080)

        layout = QVBoxLayout()
        title_label = QLabel("Exoplanet Transit")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setFixedWidth(1920)
        title_label.setFixedHeight(100)
        f = QFont("Arial", 36)
        title_label.setFont(f)

        self.main_widget = MainWidget(self.frontend_thread)

        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(title_label)
        layout.addWidget(self.main_widget)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.show()

    def refresh_transits(self, result):
        # self.main_widget.refresh_transits(result)
        self.main_widget.new_data.emit(result)

class FrontendThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(FrontendThread, self).__init__(*args, **kwargs)

        self.backend_thread = None

    def set_backend_thread(self, backend_thread):
        self.backend_thread = backend_thread

    def run(self):
        app = QApplication(sys.argv)
        qdarktheme.setup_theme()

        self.main_window = MainWindow(self)
        app.exec()

    def on_backend_job_done(self, result):
        self.main_window.refresh_transits(result)

    def request_backend_job(self, request):
        return self.backend_thread.request_job(request)