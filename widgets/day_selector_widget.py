from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, \
    QListWidget, QListWidgetItem
from PyQt6.QtGui import QFont

import datetime

class DaySelectorWidget(QWidget):
    def __init__(self, parent_widget, *args, **kwargs):
        super(DaySelectorWidget, self).__init__(*args, **kwargs)

        layout = QHBoxLayout()

        self.parent_widget = parent_widget
        self.prev_button = QPushButton("Previous day")
        self.prev_button.setFixedWidth(100)
        self.next_button = QPushButton("Next Day")
        self.next_button.setFixedWidth(100)

        self.selected_date = datetime.datetime.now().astimezone()
        self.selected_date = self.selected_date.replace(hour=12, minute=0, second=0, microsecond=0)

        self.day_label = QLabel(self.selected_date.strftime("%d %B %Y"))
        self.day_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.day_label.setFixedHeight(20)

        self.prev_button.clicked.connect(self.prev_day)
        self.next_button.clicked.connect(self.next_day)

        layout.addWidget(self.prev_button, QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
        layout.addWidget(self.day_label, QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addWidget(self.next_button, QtCore.Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

    def get_selected_date(self):
        utc_naive_date = self.selected_date.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return utc_naive_date

    def prev_day(self):
        self.selected_date = self.selected_date - datetime.timedelta(days=1)
        self.on_date_changed()

    def next_day(self):
        self.selected_date = self.selected_date + datetime.timedelta(days=1)
        self.on_date_changed()

    def on_date_changed(self):
        self.day_label.setText(self.selected_date.strftime("%d %B %Y"))
        self.parent_widget.on_date_changed()

    def set_enable_buttons(self, enabled):
        self.prev_button.setEnabled(enabled)
        self.next_button.setEnabled(enabled)