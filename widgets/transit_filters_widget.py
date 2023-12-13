from PyQt6 import QtCore

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton, QComboBox
from PyQt6.QtGui import QIntValidator,QDoubleValidator

class InputWidget(QWidget):
    def __init__(self, name, default_value="", validator=None, *args, **kwargs):
        super(InputWidget, self).__init__(*args, **kwargs)

        self.setFixedHeight(40)

        self.label = QLabel(name)
        self.label.setFixedWidth(130)
        self.input = QLineEdit(default_value)
        if validator:
            self.input.setValidator(validator)

        layout = QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.label)
        layout.addWidget(self.input)


        self.setLayout(layout)

    def get_text(self):
        return self.input.text()

    def get_float(self, default_value):
        try:
            return float(self.input.text())
        except:
            return default_value

class TransitFiltersWidget(QWidget):
    def __init__(self, parent_widget, *args, **kwargs):
        super(TransitFiltersWidget, self).__init__(*args, **kwargs)

        self.parent_widget = parent_widget

        self.setFixedWidth(300)
        self.setFixedHeight(800)

        self.long_input = InputWidget("Longitude (deg)", "26.1025", QDoubleValidator(-90, 90, 5))
        self.lat_input = InputWidget("Latitude (deg)", "44.4268", QDoubleValidator(-90, 90, 5))
        self.elevation_input = InputWidget("Elevation (m)", "75", QIntValidator())

        self.max_mag_input = InputWidget("Max Magnitude", "10", QDoubleValidator(0, 99, 2))
        self.min_dec_input = InputWidget("Min Declination (deg)", "", QDoubleValidator(-90, 90, 3))
        self.max_dec_input = InputWidget("Max Declination (deg)", "", QDoubleValidator(-90, 90, 3))
        self.min_altitude_input = InputWidget("Min Altitude (deg)", "20", QDoubleValidator(-90, 90, 3))
        self.max_sun_altitude_input = InputWidget("Max Sun Altitude (deg)", "-5", QDoubleValidator(-90, 90, 3))

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_pressed)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(QLabel("Observator"))
        layout.addWidget(self.long_input)
        layout.addWidget(self.lat_input)
        layout.addWidget(self.elevation_input)

        layout.addWidget(QLabel("Filters"))
        layout.addWidget(self.max_mag_input)
        layout.addWidget(self.min_dec_input)
        layout.addWidget(self.max_dec_input)
        layout.addWidget(self.min_altitude_input)
        layout.addWidget(self.max_sun_altitude_input)

        self.order_layout = QHBoxLayout()

        self.order_layout.addWidget(QLabel("Ordering"))

        self.ordering_widget = QComboBox()
        self.ordering_widget.addItem("Magnitude")
        self.ordering_widget.addItem("Transit depth")
        self.ordering_widget.setContentsMargins(10, 10, 10, 50)
        self.order_layout.addWidget(self.ordering_widget)
        self.order_layout.setContentsMargins(0, 10, 10, 10)

        layout.addLayout(self.order_layout)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

    def refresh_pressed(self):
        self.parent_widget.on_refresh_pressed()

    def get_observer_data(self):
        data = {
            'lon': self.long_input.get_float(22),
            'lat': self.lat_input.get_float(44),
            'height': self.elevation_input.get_float(75)
        }

        return data

    def get_filters_data(self):
        # "min_altitude": 0,
        # "sun_max_altitude": -5,
        # "dec": [-10, 50],
        # "mag": 10

        data = {}
        if self.max_mag_input.get_text():
            data["mag"] = self.max_mag_input.get_float(10)
        if self.min_dec_input.get_text() or self.max_dec_input.get_text():
            min_dec = self.min_dec_input.get_float(-90)
            max_dec = self.max_dec_input.get_float(90)
            data["dec"] = (min_dec, max_dec)
        if self.min_altitude_input.get_text():
            data["min_altitude"] = self.min_altitude_input.get_float(0)
        if self.max_sun_altitude_input.get_text():
            data["sun_max_altitude"] = self.max_sun_altitude_input.get_float(0)

        data["order"] = self.ordering_widget.currentText()

        return data

    def on_refresh_triggered(self):
        self.refresh_button.setEnabled(False)

    def on_refresh_completed(self):
        self.refresh_button.setEnabled(True)