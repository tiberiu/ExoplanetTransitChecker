from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QProgressBar

from widgets.transit_list_widget import TransitListWidget
from widgets.day_selector_widget import DaySelectorWidget

from utils import Timer

class TransitSelectorInfoWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(TransitSelectorInfoWidget, self).__init__(*args, **kwargs)

        self.resultsLabel = QLabel("Results: ")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)

        layout = QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.resultsLabel)

        self.setLayout(layout)


    def update_data(self, data):
        self.resultsLabel.setText(data.get("info", ""))
        self.progress_bar.setValue(data.get("progress", 0))

class TransitSelectorWidget(QWidget):
    def __init__(self, parent_widget, *args, **kwargs):
        super(TransitSelectorWidget, self).__init__(*args, **kwargs)

        self.parent_widget = parent_widget
        self.setFixedWidth(1500)
        self.setFixedHeight(900)

        layout = QVBoxLayout()

        self.current_page = 0
        self.transit_list_widget = TransitListWidget()
        self.day_selector_widget = DaySelectorWidget(self)
        self.info_widget = TransitSelectorInfoWidget()

        layout.addWidget(self.day_selector_widget)
        layout.addWidget(self.transit_list_widget)
        layout.addWidget(self.info_widget)

        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.setLayout(layout)

    def refresh_transits(self, data):
        self.transit_list_widget.clearTransits()

        with Timer("Adding transits"):
            for i in range(0, len(data["exoplanets"])):
                self.transit_list_widget.addTransit(data["exoplanets"][i], data)
                self.update_info_data({'progress': 70 + 30 * (i / len(data["exoplanets"])), 'info': "Generating Plots"})

    def get_selected_date(self):
        return self.day_selector_widget.get_selected_date()

    def on_date_changed(self):
        self.parent_widget.on_date_changed()

    def update_info_data(self, data):
        self.info_widget.update_data(data)

    def on_refresh_triggered(self):
        self.day_selector_widget.set_enable_buttons(False)
        self.transit_list_widget.clearTransits()

    def on_refresh_completed(self):
        self.day_selector_widget.set_enable_buttons(True)