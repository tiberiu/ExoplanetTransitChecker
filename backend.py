import datetime
import threading
import time
import math
import numpy as np

from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_sun
from astropy.time import Time
from astropy import units

import pytz
from timezonefinder import TimezoneFinder


class BackendThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(BackendThread, self).__init__(*args, **kwargs)
        self.frontend_thread = None
        self.exoplanet_db = []
        self.job = None

        self.job_lock = threading.Lock()

        self.start_time = 0
        self.stats = {}
        self.kill_signal = False

    def set_frontend_thread(self, frontend_thread):
        self.frontend_thread = frontend_thread

    def read_database(self):
        f = open("transit_db.txt", "r")
        lines = f.readlines()
        for i in range(0, len(lines), 3):
            star = lines[i].split(',')[0].strip()
            planet = lines[i].split(',')[1].strip()
            ra = list(map(float, lines[i + 1].split(', ')[0].split(' ')))
            dec = list(map(float, lines[i + 1].split(', ')[1].split(' ')))

            mag = float(lines[i + 1].split(', ')[2])
            transit_dv = float(lines[i + 1].split(', ')[3])
            duration = float(lines[i + 1].split(', ')[4])

            period = float(lines[i + 1].split(', ')[5])
            t0 = float(lines[i + 1].split(', ')[6])

            self.exoplanet_db.append({
                "star": star,
                "planet": planet,
                "ra": ra,
                "dec": dec,
                "mag": mag,
                "transit_dv": transit_dv,
                "duration": duration,
                "period": period,
                "T0": t0
            })

    def run(self):
        self.read_database()

        while True:
            time.sleep(0.1)

            job = self.get_requested_job()
            if job is not None:
                result = self.execute_job(self.job)
                self.frontend_thread.on_backend_job_done(result)
                self.clear_requested_job()

            if self.kill_signal:
                break

    def request_kill(self):
        self.kill_signal = True

    def request_job(self, request):
        with self.job_lock:
            if self.job is not None:
                return False

            self.job = request
            return True

    def get_requested_job(self):
        with self.job_lock:
            return self.job

    def clear_requested_job(self):
        with self.job_lock:
            self.job = None

    def job_started(self):
        self.start_time = time.time()
        self.stats = {}

    def job_ended(self):
        duration = time.time() - self.start_time
        print("Job took: %.2f seconds" % duration)
        print("Stats:")
        for key in self.stats:
            print("%s: %d" % (key, self.stats[key]))

    def add_stat(self, key, value):
        if key not in self.stats:
            self.stats[key] = 0

        self.stats[key] += value

    def execute_job(self, job):
        self.job_started()
        result = self.execute_job_internal(job)
        self.job_ended()

        return result

    def get_observer_timezone(self, observer_data):
        tzf = TimezoneFinder()
        local_tz = pytz.timezone(tzf.timezone_at(lng=observer_data["lon"], lat=observer_data["lat"]))

        return local_tz

    def timezone_transform(self, date, observer_data):
        local_tz = self.get_observer_timezone(observer_data)
        local_date = date.astimezone(local_tz).replace(hour=12, minute=0, second=0, microsecond=0)

        # For UTC date we convert it to UTC to apply the timedelta, and after we remove the tzinfo
        # becase we need it as a naive date in further calculations
        utc_date = local_date.astimezone(pytz.utc).replace(tzinfo=None)

        return utc_date

    def execute_job_internal(self, job):
        start_date_utc = self.timezone_transform(job["start_date"], job["observer"])
        end_date_utc = self.timezone_transform(job["end_date"], job["observer"])

        start_hjd = Time(start_date_utc, format='datetime').jd
        end_hjd = Time(end_date_utc, format='datetime').jd

        exoplanets = []
        sun_alt_graph = self.get_sun_alt_graph(job)

        exoplanets_to_plot = []
        exoplanet_transits = []
        for exoplanet in self.exoplanet_db:
            if not self.apply_exoplanet_filters(exoplanet, job["observer"], job["filters"]):
                self.add_stat("Exoplanets Reject by star", 1)
                continue

            self.add_stat("Exoplanets Analized", 1)

            x = start_hjd - exoplanet['T0']
            jd_duration = exoplanet["duration"] / 1440
            transits_since_t0 = math.floor(x / exoplanet['period'])
            last_transit_start = transits_since_t0 * exoplanet['period'] + exoplanet['T0'] - jd_duration / 2

            transits = []
            while last_transit_start < end_hjd:
                if last_transit_start + jd_duration > start_hjd:
                    transits.append({"start": Time(last_transit_start, format="jd").to_datetime(),
                                     "end": Time(last_transit_start + jd_duration, format="jd").to_datetime(),
                                     "valid": True})

                last_transit_start = last_transit_start + exoplanet["period"]

            if len(transits) == 0:
                continue

            exoplanets_to_plot.append(exoplanet)
            exoplanet_transits.append(transits)

        plot_graphs = self.generate_altitude_graphs(exoplanets_to_plot, job)

        for ex_id in range(0, len(exoplanets_to_plot)):
            # compute alt graph
            alt_graph = plot_graphs[ex_id]
            transits = exoplanet_transits[ex_id]
            exoplanet = exoplanets_to_plot[ex_id]
            self.add_stat("Exoplanet plots calculated", 1)

            has_valid_transits = False
            for transit in transits:
                start_min = int((transit["start"] - start_date_utc).total_seconds() / 60)
                duration_mins = int(exoplanet["duration"])

                end_min = int((transit["end"] - start_date_utc).total_seconds() / 60)
                end_min = min(end_min, int((end_date_utc - start_date_utc).total_seconds() / 60))

                max_sun_alt = job["filters"].get("sun_max_altitude", 90)

                for i in range(max(start_min, 0), min(end_min, start_min + duration_mins)):
                    if alt_graph["y"][i] < job["filters"].get("min_altitude", 0):
                        transit["valid"] = False
                        break

                    if sun_alt_graph["y"][i] > max_sun_alt:
                        transit["valid"] = False
                        break

                if transit["valid"]:
                    has_valid_transits = True

            if has_valid_transits:
                self.add_stat("Exoplanet Added", 1)
                exoplanets.append({"exoplanet_details": exoplanet, "transits": transits, "alt_graph": alt_graph})

        exoplanets = self.sort_exoplanets(exoplanets, job["filters"]["order"])

        print("Backend job done")

        return {"exoplanets": exoplanets, "sun_alt_graph": sun_alt_graph, "start_date": start_date_utc, "end_date": end_date_utc,
                "observer_timezone": self.get_observer_timezone(job["observer"])}

    def sort_exoplanets(self, exoplanets, order):
        cmp = None
        print(exoplanets)
        if order == "Magnitude":
            cmp = lambda item: item["exoplanet_details"]["mag"]
        elif order == "Transit depth":
            cmp = lambda item: 1 - item["exoplanet_details"]["transit_dv"]
        else:
            print("No sorting")
            return exoplanets

        exoplanets = sorted(exoplanets, key=cmp)
        return exoplanets

    def apply_exoplanet_filters(self, exoplanet_details, observer, filters):
        # filter dec
        dec = exoplanet_details["dec"][0]
        if "dec" in filters:
            min_dec, max_dec = filters["dec"]
        else:
            # if no dec filter, filter stars that are never visible
            min_dec = -90
            max_dec = 90
            lat = observer["lat"]
            if lat > 0:
                min_dec = lat - 90
            else:
                max_dec = 90 + lat

        if dec < min_dec or dec > max_dec:
            return False

        # filter mag
        if "mag" in filters:
            max_mag = filters["mag"]
            if exoplanet_details["mag"] > max_mag:
                return False

        return True

    def generate_altitude_graphs(self, exoplanets, job):
        observer_location = EarthLocation(lat=job["observer"]["lat"],
                                          lon=job["observer"]["lon"],
                                          height=job["observer"]["height"] * units.m)

        ras = []
        decs = []
        cnt = 0
        for exoplanet in exoplanets:
            ra = exoplanet["ra"]
            dec = exoplanet["dec"]

            ras.append("%dh%dm%.2fs" % (ra[0], ra[1], ra[2]))
            decs.append("%dd%dm%.2fs" % (dec[0], dec[1], dec[2]))

        star_coordinates = SkyCoord(ra=ras,
                                    dec=decs,
                                    unit=(units.hourangle, units.deg), frame='icrs')

        start_date_utc = self.timezone_transform(job["start_date"], job["observer"])
        end_date_utc = self.timezone_transform(job["end_date"], job["observer"])

        min_count = (end_date_utc - start_date_utc).total_seconds() // 60
        observation_datetimes = []
        for i in range(0, int(min_count)):
            date = start_date_utc + datetime.timedelta(minutes=i)
            observation_datetimes.append([date])

        observation_times = Time(observation_datetimes, format='datetime')

        # Transform the equatorial coordinates to Altitude/Azimuth for the observer's location and time
        start_time = time.time()
        altaz_coordinates = star_coordinates.transform_to(AltAz(obstime=observation_times, location=observer_location))
        print("AltAz computation: %.2f" % (time.time() - start_time))

        graphs = []
        for ex_id in range(0, len(exoplanets)):
            x = np.arange(0, min_count)
            y = altaz_coordinates[:,ex_id].alt.value
            graphs.append({"x": x, "y": y})

        return graphs

    def get_sun_alt_graph(self, job):
        observer_location = EarthLocation(lat=job["observer"]["lat"],
                                          lon=job["observer"]["lon"],
                                          height=job["observer"]["height"] * units.m)

        start_date_utc = self.timezone_transform(job["start_date"], job["observer"])
        end_date_utc = self.timezone_transform(job["end_date"], job["observer"])

        sun_coord = get_sun(Time(start_date_utc, format='datetime'))
        observation_dtimes = []
        min_count = (end_date_utc - start_date_utc).total_seconds() // 60
        for i in range(0, int(min_count)):
            observation_dtimes.append(start_date_utc + datetime.timedelta(minutes=i))

        sun_altaz = sun_coord.transform_to(AltAz(obstime=Time(observation_dtimes, format='datetime'),
                                                 location=observer_location))

        x = []
        y = []
        for i in range(0, int(min_count)):
            x.append(i)
            y.append((sun_altaz[i].alt * units.deg).value)

        return {"x": x, "y": y}
