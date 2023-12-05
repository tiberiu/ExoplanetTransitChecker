from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, \
    QListWidget, QListWidgetItem
from PyQt6.QtGui import QFont

import datetime

from widgets.transit_selector_widget import TransitSelectorWidget
from widgets.transit_filters_widget import TransitFiltersWidget

class MainWidget(QWidget):
    new_data = QtCore.pyqtSignal(dict)

    def __init__(self, frontend_thread, *args, **kwargs):
        super(MainWidget, self).__init__(*args, **kwargs)

        self.frontend_thread = frontend_thread
        self.setFixedHeight(900)

        self.new_data.connect(self.refresh_transits)

        layout = QHBoxLayout()

        self.transit_selector_widget = TransitSelectorWidget(self)
        self.transit_filters_widget = TransitFiltersWidget(self)

        layout.addWidget(self.transit_selector_widget)
        layout.addWidget(self.transit_filters_widget)

        self.setLayout(layout)

        self.trigger_recompute_transits()

    def on_date_changed(self):
        self.trigger_recompute_transits()

    def on_refresh_pressed(self):
        self.trigger_recompute_transits()

    def trigger_recompute_transits(self):
        start_date = self.transit_selector_widget.get_selected_date()
        end_date = start_date + datetime.timedelta(days=1)

        observer_data = self.transit_filters_widget.get_observer_data()
        filters_data = self.transit_filters_widget.get_filters_data()

        self.transit_selector_widget.update_info_data({'progress': 0, 'info': "Searching"})

        """
        request = {"start_date": start_date, "end_date": end_date,
                   "observer": {
                        'lon': 44.49239,
                        'lat': 26.02435,
                        'height' : 75,
                   },
                   "filters": {
                       "min_altitude": 0,
                       "sun_max_altitude": -5,
                       "dec": [-10, 50],
                       "mag": 10
                   }}
        """
        request = {
            "start_date": start_date,
            "end_date": end_date,
            "observer": observer_data,
            "filters": filters_data
        }

        print("Starting job for request: %s" % request)

        self.transit_selector_widget.on_refresh_triggered()
        self.transit_filters_widget.on_refresh_triggered()

        self.frontend_thread.request_backend_job(request)

    def refresh_transits(self, result):
        print("Got result. %d transits found" % (len(result["exoplanets"])))
        self.transit_selector_widget.update_info_data({'progress': 70, 'info': "Generating Plots"})
        self.transit_selector_widget.refresh_transits(result)
        self.transit_selector_widget.update_info_data({'progress': 100, 'info': "Results: %d" % len(result["exoplanets"])})

        self.transit_selector_widget.on_refresh_completed()
        self.transit_filters_widget.on_refresh_completed()