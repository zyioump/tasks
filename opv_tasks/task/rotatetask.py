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
# Description: Manage picture rotation in portrait mode

import exifread
import os
from path import Path

from opv_tasks import Task
from opv_tasks import run_cli

class RotateTask(Task):
    """
        Manage rotation for source set of images.

        As they need to be in portrait mode.
    """

    def getPictureSizes(self, picPath):
        """
        return (width, height) of the specified picture (picPath)
        """
        with open(picPath, "rb") as pic:
            tags = exifread.process_file(pic, stop_tag='EXIF ExifImageWidth')

        return (tags['EXIF ExifImageWidth'], tags['EXIF ExifImageLength'])

    def isPortrait(self, picPath: str):
        """
        return true if a picture is in portrait mode
        """
        x, y = self.getPicturesSizes(picPath)
        return x < y

    def rotatePic(self, rotation_angle, picPath):
        """
        Rotate picPath with rotation_angle.
        Modify picture in place !
        """
        run_cli('mogrify', ["-rotate", rotation_angle, picPath])  # TODO : test

    def rotateToPortrait(self, picPath):
        """
        Rotate a picture to portrait format if necessary.
        """
        if self.isPortrait(picPath):
            self.rotatePic(90, picPath)

    def rotateToPortraitAll(self):
        """
        Rotate all picture of lot to portrait
        """
        if self.lot is not None and self.lot.pictures_path is not None:
            with self._opv_directory_manager.Open(self.lot.pictures_path) as (uuid, dir_path):
                for apnNo in range(0,5):
                    pic_path = Path(dir_path) / "APN{}.JPG".format(apnNo)
                    if os.path.exists(pic_path):
                        self.rotateToPortrait(pic_path)

    def run(self, options={}):
        if "lotId" in options:
            self.lot = self._client_requestor.Lot(options["lotId"])
            self.rotateToPortraitAll()
