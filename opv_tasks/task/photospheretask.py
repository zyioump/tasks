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

# Contributors: tristan GOUGE <gouge.tristan@openpathview.fr>
# Email: team@openpathview.fr

import json
import os

from path import Path
from .task import Task
from opv_api_client import ressources

from opv_tasks.const import Const

from libxmp import XMPFiles, consts
from PIL import Image

import logging

class PhotosphereTask(Task):
    """
    Convert the panorama to google's photosphere format.
    Input format :
        opv-task photosphere '{"id_panorama": ID_PANORAMA, "id_malette": ID_MALETTE }'
    Output format :
        {"id_panorama": ID_PANORAMA, "id_malette": ID_MALETTE }
    """

    TASK_NAME = "photosphere"
    requiredArgsKeys = ["id_panorama", "id_malette"]

    def to_deg(self, value, loc):
        if value < 0:
            loc_value = loc[0]
        elif value > 0:
            loc_value = loc[1]
        else:
            loc_value = ""
        abs_value = abs(value)
        deg =  int(abs_value)
        t1 = (abs_value-deg)*60
        min = int(t1)
        sec = round((t1 - min)* 60, 5)
        return (deg, min, sec, loc_value)

    def convert(self, picture_dir):
        picture_path = picture_dir / Const.PANO_FILENAME

        with Image.open(picture_path) as im:
            width, height = im.size

        xmpfile = XMPFiles(file_path=picture_path, open_forupdate=True)
        xmp = xmpfile.get_xmp()

        # see https://developers.google.com/streetview/spherical-metadata
        PHOTOSPHERE_NS = "http://ns.google.com/photos/1.0/panorama/"

        xmp.set_property(PHOTOSPHERE_NS, "GPano:ProjectionType", "equirectangular")

        heading_degree = self.panorama.cp.lot.sensors.degrees + self.panorama.cp.lot.sensors.minutes / 60
        xmp.set_property_float(PHOTOSPHERE_NS, "GPano:PoseHeadingDegrees", heading_degree)

        xmp.set_property_int(PHOTOSPHERE_NS, "GPano:CroppedAreaImageWidthPixels", width)
        xmp.set_property_int(PHOTOSPHERE_NS, "GPano:CroppedAreaImageHeightPixels", height)

        xmp.set_property_int(PHOTOSPHERE_NS, "GPano:CroppedAreaLeftPixels", 0)
        xmp.set_property_int(PHOTOSPHERE_NS, "GPano:CroppedAreaTopPixels", 0)

        xmp.set_property_int(PHOTOSPHERE_NS, "GPano:FullPanoWidthPixels", width)
        xmp.set_property_int(PHOTOSPHERE_NS, "GPano:FullPanoHeightPixels", height)

        xmpfile.can_put_xmp(xmp)
        xmpfile.put_xmp(xmp)
        xmpfile.close_file()

        lat_deg = self.to_deg(self.panorama.cp.lot.sensors.gps_pos["coordinates"][0], ["S", "N"])
        lng_deg = self.to_deg(self.panorama.cp.lot.sensors.gps_pos["coordinates"][1], ["W", "E"])

        self._run_cli("exiftool",["-exif:gpslatitude='"+str(lat_deg[0])+" "+str(lat_deg[1])+" "+str(lat_deg[2])+"'", "-exif:gpslatituderef="+str(lat_deg[3]), picture_path], stdout_level=logging.DEBUG, stderr_level=logging.DEBUG)
        self._run_cli("exiftool",["-exif:gpslongitude='"+str(lng_deg[0])+" "+str(lng_deg[1])+" "+str(lng_deg[2])+"'", "-exif:gpslongituderef="+str(lng_deg[3]), picture_path], stdout_level=logging.DEBUG, stderr_level=logging.DEBUG)
        self._run_cli("exiftool",["-exif:gpsaltitude='"+str(self.panorama.cp.lot.sensors.gps_pos["coordinates"][2])+"'", picture_path], stdout_level=logging.DEBUG, stderr_level=logging.DEBUG)
        self._run_cli("rm", [picture_path+"_original"], stdout_level=logging.DEBUG, stderr_level=logging.DEBUG)

        self.panorama.is_photosphere = True
        self.panorama.save()

    def runWithExceptions(self, options={}):
        """Run a StitchTask with options."""

        self.checkArgs(options)

        self.panorama = self._client_requestor.make(ressources.Panorama, options["id_panorama"], options["id_malette"])
        with self._opv_directory_manager.Open(self.panorama.equirectangular_path) as (_, picture_path):
            self.convert(Path(picture_path))

        return self.panorama.id
