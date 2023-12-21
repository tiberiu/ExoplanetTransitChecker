from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, \
    QListWidget, QListWidgetItem
from PyQt6.QtGui import QFont

from widgets.transit_plot_widget import TransitPlotWidget
import datetime

import urllib

ETD_ROOT = 'http://var2.astro.cz/ETD/'
ETD_PREDICT_URL = ETD_ROOT + "predict_detail.php"

class TransitListWidgetItem(QWidget):
    def __init__(self, transit_data, result_data, *args, **kwargs):
        super(TransitListWidgetItem, self).__init__(*args, **kwargs)

        start_date = result_data["start_date"]
        end_date = result_data["end_date"]
        observer_tz = result_data["observer_timezone"]
        observer_lon = result_data["observer"]["lon"]
        observer_lat = result_data["observer"]["lat"]
        sun_alt_graph = result_data["sun_alt_graph"]

        local_start_date = start_date.replace(tzinfo=datetime.timezone.utc).astimezone(observer_tz)
        local_end_date = end_date.replace(tzinfo=datetime.timezone.utc).astimezone(observer_tz)

        self.pltWidget = TransitPlotWidget(self, width=4, height=3, dpi=100)
        self.pltWidget.create_plot(transit_data, sun_alt_graph, local_start_date, local_end_date, observer_tz)

        layout = QHBoxLayout()

        starInfoLayout = QVBoxLayout()
        starInfoLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        starInfoLayout.addWidget(QLabel("Star: %s" % transit_data["exoplanet_details"]['star']))
        starInfoLayout.addWidget(QLabel("Planet: %s" % transit_data["exoplanet_details"]['planet']))
        starInfoLayout.addWidget(QLabel("RA: %d h %d m %.2f s" % (transit_data["exoplanet_details"]['ra'][0],
                                                                transit_data["exoplanet_details"]['ra'][1],
                                                                transit_data["exoplanet_details"]['ra'][2])
                                        )
                                 )

        starInfoLayout.addWidget(QLabel("DEC: %d° %d' %.2f''" % (transit_data["exoplanet_details"]['dec'][0],
                                                                   transit_data["exoplanet_details"]['dec'][1],
                                                                   transit_data["exoplanet_details"]['dec'][2])
                                        )
                                 )
        starInfoLayout.addWidget(QLabel("Mag: %s" % transit_data["exoplanet_details"]['mag']))
        starInfoLayout.addWidget(QLabel("Transit Delta Mag: %s" % transit_data["exoplanet_details"]["transit_dv"]))
        starInfoLayout.addWidget(QLabel("Transit Duration: %s mins" % transit_data["exoplanet_details"]["duration"]))

        total_seconds = datetime.timedelta(transit_data["exoplanet_details"]["period"]).total_seconds()
        pdays = total_seconds // 86400
        phours = (total_seconds - pdays * 86400) // 3600
        pminutes = (total_seconds - pdays * 86400 - phours * 3600) // 60
        starInfoLayout.addWidget(QLabel("Transit Period: %d days %d hours %d minutes" % (pdays, phours, pminutes)))

        etd_link = ETD_PREDICT_URL + "?" + urllib.parse.urlencode({"STARNAME": transit_data["exoplanet_details"]["star"],
                                                                   "PLANET": transit_data["exoplanet_details"]["planet"],
                                                                   'submit': 'submit',
                                                                   'delka': observer_lon, 'sirka': observer_lat})
        link_label = QLabel()
        link_label.setText('<a href="%s">More Details - ETD Link</a>' % etd_link)
        link_label.setOpenExternalLinks(True)
        starInfoLayout.addWidget(link_label)

        for i in range(0, len(transit_data["transits"])):
            transit = transit_data["transits"][i]
            start = transit["start"].replace(tzinfo=datetime.timezone.utc).astimezone(observer_tz)
            end = transit["end"].replace(tzinfo=datetime.timezone.utc).astimezone(observer_tz)
            transit_label = QLabel("Transit: %s - %s" % (start.strftime("%H:%M %d.%m.%Y"), end.strftime("%H:%M %d.%m.%Y")))
            starInfoLayout.addWidget(transit_label)

        layout.addLayout(starInfoLayout)
        layout.addWidget(self.pltWidget)

        self.setLayout(layout)

class TransitListWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(TransitListWidget, self).__init__(*args, **kwargs)

        layout = QVBoxLayout()

        self.list_widget = QListWidget(self)

        layout.addWidget(self.list_widget)

        self.setLayout(layout)

    def addTransit(self, transit_data, result_data):
        item = QListWidgetItem(self.list_widget)
        itemWidget = TransitListWidgetItem(transit_data, result_data)
        item.setSizeHint(itemWidget.sizeHint())

        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, itemWidget)

    def clearTransits(self):
        self.list_widget.clear()