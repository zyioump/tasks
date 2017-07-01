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

from PIL import Image
import os
from path import Path

from opv_api_client import ressources

from opv_tasks.task import Task
from opv_tasks.task import TaskReturn
from opv_tasks.task import TaskStatusCode


class RotateTask(Task):
    """
    Manage rotation for source set of images.

    As they need to be in portrait mode.
    """

    TASK_NAME = "rotate"

    def getPictureSizes(self, picPath):
        """Return (width, height) of the specified picture (picPath)."""
        with Image.open(picPath) as pic:
            width, height = pic.size

        return (width, height)

    def isPortrait(self, picPath):
        """Return true if a picture is in portrait mode."""
        x, y = self.getPictureSizes(picPath)
        self.logger.debug("Width: " + str(x) + "  Height: " + str(y))
        return x < y

    def rotatePic(self, rotation_angle, picPath):
        """
        Rotate picPath with rotation_angle.

        Modify picture in place !
        """
        self.logger.debug("Rotate pic " + picPath + " angle : " + str(rotation_angle))
        cli_code = self._run_cli('mogrify', ["-rotate", str(rotation_angle), picPath])

        if cli_code != 0:
            raise RotateException(picPath, rotation_angle)

    def rotateToPortrait(self, picPath):
        """Rotate a picture to portrait format if necessary."""
        if not self.isPortrait(picPath):
            self.rotatePic(90, picPath)

    def rotateToPortraitAll(self):
        """Rotate all picture of lot to portrait."""
        if self.lot is not None and self.lot.pictures_path is not None:
            with self._opv_directory_manager.Open(self.lot.pictures_path) as (uuid, dir_path):
                for apnNo in range(0, 6):
                    pic_path = Path(dir_path) / "APN{}.JPG".format(apnNo)
                    if os.path.exists(pic_path):
                        try:
                            self.rotateToPortrait(pic_path)
                        except RotateException as e:
                            self.taskReturn.statusCode = TaskStatusCode.ERROR
                            self.taskReturn.error = str(e)
                    else:
                        self.taskReturn.statusCode = TaskStatusCode.ERROR
                        self.taskReturn.error = "Picture file for APN" + str(apnNo) + \
                            " not found (uuid : " + str(uuid) + " / lot.id : " + str(self.lot.id) + ")"
                        self.logger.error(self.taskReturn.error)
                        return

    def run(self, options={}):
        """
            Run a rotatetask.
            Requires id_lot and id_malette as inputData.
        """
        if "id_lot" in options and "id_malette" in options:
            self.taskReturn = TaskReturn(taskName=self.TASK_NAME, inputData=options)
            self.lot = self._client_requestor.make(ressources.Lot, options['id_lot'], options['id_malette'])
            self.rotateToPortraitAll()
            self.taskReturn.outputData = options

        return self.taskReturn


class RotateException(Exception):
    """
    Raised when file rotation fail.
    """

    def __init__(self, filePath, rotationAngle):
        self.filePath = filePath
        self.rotationAngle = rotationAngle

    def __str__(self):
        return "Failled to rotate " + str(self.filePath) + ", with rotation angle : " + str(self.rotationAngle)
