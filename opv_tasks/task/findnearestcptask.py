# coding: utf-8

# Copyright (C) 2017 Open Path View, Maison Du Libre
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

# Contributors: Benjamin BERNARD <benjamin.bernard@openpathview.fr>
# Email: team@openpathview.fr
# Description: Task to get the nearest stitchable cp

from opv_tasks.task import Task
from opv_api_client import ressources, Filter
from math import sin, cos, sqrt, atan2, radians
from collections import OrderedDict
import requests

class FindnearestcpTask(Task):
    """
    Find nearest stitchable cp. Takes lot in input (id_lot and id_malette needed).
    Input format :
        opv-task findnearestcp '{"id_lot": ID_LOT, "id_malette": ID_MALETTE }'
    Output format :
        {"id_cp": ID_CP, "id_malette": ID_MALETTE }
    """

    TASK_NAME = "findnearestcp"
    requiredArgsKeys = ["id_lot", "id_malette"]

    EARTH_RADIUS = 6373.0

    def distance(self, gpsPosA, gpsPosB):
        """
        Compute distance in meters beween 2 gps position.

        :param gpsPosA: First GPS position {"coordinates": [LAT, LON]}
        :param gpsPosB: Second GPS position {"coordinates": [LAT, LON]}
        :return: Distance in meters.
        """
        # approximate radius of earth in km
        lat1 = radians(gpsPosA['coordinates'][0])
        lon1 = radians(gpsPosA['coordinates'][1])
        lat2 = radians(gpsPosB['coordinates'][0])
        lon2 = radians(gpsPosA['coordinates'][1])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = self.EARTH_RADIUS * c
        return distance

    def runWithExceptions(self, options={}):
        """
        Search nearest cp stitchable to inject it.

        :param options: {"id_lot": ID, "id_malette": ID}
        """

        self.logger.debug("Options : " + str(options))
        self.checkArgs(options)
        lot = self._client_requestor.make(ressources.Lot, options["id_lot"], options["id_malette"])
        nearestSensors = self._client_requestor.make_all(ressources.Sensors,
                                                         filters=(Filter.within([lot.sensors.id_sensors,
                                                                  lot.sensors.id_malette], 30)))
        self.logger.debug(nearestSensors)
        nearestSensorsWithDistance = []

        # computing distances, with tuple (dist, sensor)
        for s in nearestSensors:
            self.logger.debug(s)
            nearestSensorsWithDistance.append((self.distance(s.gps_pos, lot.sensors.gps_pos), s))

        # sorting it
        nearestSensorsWithDistance = sorted(nearestSensorsWithDistance, key=lambda sensorTuple: sensorTuple[0])
        self.logger.debug(str(nearestSensorsWithDistance))

        # filtering it
        # remove it self
        self.logger.debug(len(nearestSensorsWithDistance))
        nearestSensorsWithDistanceFiltered = []
        self.logger.debug("-- Filtering --")
        for sensorWithDistance in nearestSensorsWithDistance:
            s = sensorWithDistance[1]
            if not(s.lot.id_lot == lot.id_lot and s.lot.id_malette == lot.id_malette):
                nearestSensorsWithDistanceFiltered.append(sensorWithDistance)

        self.logger.debug(nearestSensorsWithDistanceFiltered)
        self.logger.debug(len(nearestSensorsWithDistanceFiltered))

        # finding nearest stitchable
        for sensorDist in nearestSensorsWithDistanceFiltered:
            _, sensor = sensorDist
            associatedLot = sensor.lot
            if associatedLot.tile is not None:
                self.logger.debug("Found CP " + str(associatedLot.cps[0]))
                out = {}
                out['id_cp'] = associatedLot.cps[0].id_cp
                out['id_malette'] = associatedLot.cps[0].id_malette
                return out

        # TODO should throw an exception
        return None
