"Simple parser for Garmin TCX files."

import time

from lxml import objectify

namespace = 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'
ext_namespace = 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'


class TCXParser(object):
    def __init__(self, tcx_file):
        tree = objectify.parse(tcx_file)
        self.root = tree.getroot()
        self.activity = self.root.Activities.Activity

    def hr_values(self):
        return [x.pyval for x in self.root.xpath('//ns:HeartRateBpm/ns:Value', namespaces={'ns': namespace})]

    def altitude_points(self):
        return [x.pyval for x in self.root.xpath('//ns:AltitudeMeters', namespaces={'ns': namespace})]

    def time_values(self):
        return [x.text for x in self.root.xpath('//ns:Time', namespaces={'ns': namespace})]

    def speed_values(self):
        return [x.pyval for x in self.root.xpath('//ns:Trackpoint//ns:Extensions//ns2:TPX//ns2:Speed',
                                                 namespaces={'ns': namespace, 'ns2': ext_namespace})]

    def all_trackpoints(self):
        points = list()
        for x in self.root.xpath('//ns:Trackpoint', namespaces={'ns': namespace}):
            if hasattr(x,'Position'):
                points.append(Trackpoint(x.Position.LatitudeDegrees.pyval, x.Position.LongitudeDegrees.pyval, x.Time.pyval))
        return points

    @property
    def latitude(self):
        if hasattr(self.activity.Lap.Track.Trackpoint, 'Position'):
            return self.activity.Lap.Track.Trackpoint.Position.LatitudeDegrees.pyval

    @property
    def longitude(self):
        if hasattr(self.activity.Lap.Track.Trackpoint, 'Position'):
            return self.activity.Lap.Track.Trackpoint.Position.LongitudeDegrees.pyval

    @property
    def activity_type(self):
        return self.activity.attrib['Sport'].lower()

    @property
    def completed_at(self):
        return self.activity.Lap[-1].Track.Trackpoint[-1].Time.pyval

    @property
    def distance(self):
        distance_values = self.root.findall('.//ns:DistanceMeters', namespaces={'ns': namespace})
        if distance_values:
            return distance_values[-1]
        return 0

    @property
    def distance_units(self):
        return 'meters'

    @property
    def duration(self):
        """Returns duration of workout in seconds."""
        return sum(lap.TotalTimeSeconds for lap in self.activity.Lap)

    @property
    def calories(self):
        return sum(lap.Calories for lap in self.activity.Lap)

    @property
    def hr_avg(self):
        """Average heart rate of the workout, 0 if unable to calculate"""
        hr_data = self.hr_values()
        if len(hr_data) < 1:
            return 0
        else:
            return sum(hr_data) / len(hr_data)

    @property
    def hr_max(self):
        """Minimum heart rate of the workout"""
        return max(self.hr_values())

    @property
    def hr_min(self):
        """Minimum heart rate of the workout"""
        return min(self.hr_values())

    @property
    def pace(self):
        """Average pace (mm:ss/km for the workout"""
        secs_per_km = self.duration / (self.distance / 1000)
        return time.strftime('%M:%S', time.gmtime(secs_per_km))

    @property
    def speed_min(self):
        """Minimum speed of the workout"""
        return min(self.speed_values())

    @property
    def speed_max(self):
        """Maximum speed of the workout"""
        return max(self.speed_values())

    @property
    def speed_avg(self):
        """Average speed of the workout, 0 if unable to calculate"""
        speed_data = self.speed_values()
        if len(speed_data) < 1:
            return 0
        else:
            return sum(speed_data) / len(speed_data)

    @property
    def speed_units(self):
        return 'm/s'

    @property
    def altitude_avg(self):
        """Average altitude for the workout, 0 if unable to calculate"""
        altitude_data = self.altitude_points()
        if len(altitude_data) < 1:
            return 0
        else:
            return sum(altitude_data) / len(altitude_data)

    @property
    def altitude_max(self):
        """Max altitude for the workout"""
        altitude_data = self.altitude_points()
        return max(altitude_data)

    @property
    def altitude_min(self):
        """Min altitude for the workout"""
        altitude_data = self.altitude_points()
        return min(altitude_data)

    @property
    def ascent(self):
        """Returns ascent of workout in meters"""
        total_ascent = 0.0
        altitude_data = self.altitude_points()
        for i in range(len(altitude_data) - 1):
            diff = altitude_data[i + 1] - altitude_data[i]
            if diff > 0.0:
                total_ascent += diff
        return total_ascent

    @property
    def descent(self):
        """Returns descent of workout in meters"""
        total_descent = 0.0
        altitude_data = self.altitude_points()
        for i in range(len(altitude_data) - 1):
            diff = altitude_data[i + 1] - altitude_data[i]
            if diff < 0.0:
                total_descent += abs(diff)
        return total_descent


class Trackpoint(object):

    def __init__(self, lat, lng, time):
        self.latitude = lat
        self.longitude = lng
        self.time = time

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        self._time = value

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, value):
        self._latitude = value

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, value):
        self._longitude = value
