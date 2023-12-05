from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Rectangle
from matplotlib import colormaps
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import Formatter
import numpy as np

import datetime

class TimeFormatter(Formatter):
    def __init__(self, start_date):
        self.start_date = start_date

    def __call__(self, x, pos):
        date = self.start_date + datetime.timedelta(minutes=int(x))
        date = date.replace(tzinfo=datetime.timezone.utc).astimezone()
        return date.strftime("%H:%M")

class TransitPlotWidget(FigureCanvasQTAgg):
    def get_sky_color(self, sun_alt):
        day_color = (173 / 255, 216 / 255, 230 / 255)
        night_color = (5 / 255, 5 / 255, 35 / 255)

        color = day_color
        if sun_alt < 5 and sun_alt > -5:
            t = (sun_alt + 5) / 10
            color = (day_color[0] * t + night_color[0] * (1 - t),
                            day_color[1] * t + night_color[1] * (1 - t),
                            day_color[2] * t + night_color[2] * (1 - t))
        if sun_alt < -5:
            color = night_color

        return color

    def create_plot(self, transit_data, sun_alt_graph, start_date, end_date):
        x = transit_data["alt_graph"]["x"]
        y = transit_data["alt_graph"]["y"]
        transit_list = transit_data["transits"]

        segments = []
        colors = []
        patches = []
        patch_colors = []
        for i in range(1, len(x)):
            segments.append([(x[i - 1], y[i - 1]), (x[i], y[i])])

            date = start_date + datetime.timedelta(minutes=i)
            in_transit = False
            for t in transit_list:
                if t["start"] < date and date < t["end"]:
                    in_transit = True
                    break

            if in_transit:
                colors.append("red")
            else:
                colors.append("blue")

            patches.append(Rectangle((i, -90), 1, 180))
            patch_colors.append(self.get_sky_color(0.5 - sun_alt_graph["y"][i])[1] * 0.5)

        sky_color = LinearSegmentedColormap.from_list("sky", [(173 / 255, 216 / 255, 230 / 255), (5 / 255, 5 / 255, 35 / 255)])
        patch_collection = PatchCollection(patches, cmap=sky_color)
        patch_collection.set_array(patch_colors)
        lc = LineCollection(segments, colors=colors)
        self.axes.add_collection(lc)
        self.axes.add_collection(patch_collection)
        self.axes.set_ylim(0, 90)
        self.axes.set_xlim(0, 1440)
        # self.axes.set_xticklabels([1, 2, 3, 4, 5, 6, 7])
        self.axes.xaxis.set_major_formatter(TimeFormatter(start_date))
        self.axes.xaxis.set_ticks(np.arange(0, 1440, 60))
        self.axes.tick_params(axis='x', labelrotation=45)

        self.fig.tight_layout()


    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.fig.set_facecolor('#75a8f6')
        super(TransitPlotWidget, self).__init__(self.fig)