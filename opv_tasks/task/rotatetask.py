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
""" Roate Task, will rotate pictures from a lot

Usage:
    opv-task-rotate <id-lot> [--db-rest=<str>] [--dir-manager=<str>] [--debug]
    opv-task-rotate (-h | --help)

Options:
    -h --help                Show help.
    --db-rest=<str>          API rest server [default: http://localhost:5000]
    --dir-manager=<str>      API for directory manager [default: http://localhost:5001]
    --debug                  Debug mode.
"""

from PIL import Image
import os
import logging
import json
from path import Path
from docopt import docopt

from opv_tasks.task import Task

class RotateTask(Task):
    """
        Manage rotation for source set of images.

        As they need to be in portrait mode.
    """

    def getPictureSizes(self, picPath):
        """
        return (width, height) of the specified picture (picPath)
        """
        with Image.open(picPath) as pic:
            width, height = pic.size

        return (width, height)

    def isPortrait(self, picPath: str):
        """
        return true if a picture is in portrait mode
        """
        x, y = self.getPictureSizes(picPath)
        logging.debug("Width: " + str(x) + "  Height: " + str(y))
        return x < y

    def rotatePic(self, rotation_angle, picPath):
        """
        Rotate picPath with rotation_angle.
        Modify picture in place !
        """
        logging.debug("Rotate pic " + picPath + " angle : " + str(rotation_angle))
        self._run_cli('mogrify', ["-rotate", str(rotation_angle), picPath])  # TODO : test

    def rotateToPortrait(self, picPath):
        """
        Rotate a picture to portrait format if necessary.
        """
        if not self.isPortrait(picPath):
            self.rotatePic(90, picPath)

    def rotateToPortraitAll(self):
        """
        Rotate all picture of lot to portrait
        """
        if self.lot is not None and self.lot.pictures_path is not None:
            with self._opv_directory_manager.Open(self.lot.pictures_path) as (uuid, dir_path):
                for apnNo in range(0, 6):
                    pic_path = Path(dir_path) / "APN{}.JPG".format(apnNo)
                    if os.path.exists(pic_path):
                        self.rotateToPortrait(pic_path)

    def run(self, options={}):
        if "lotId" in options:
            self.lot = self._client_requestor.Lot(options["lotId"])
            self.rotateToPortraitAll()

        return json.dumps({})


def main():
    from opv_directorymanagerclient import DirectoryManagerClient, Protocol
    from potion_client import Client

    arguments = docopt(__doc__)
    debug = bool(arguments.get('--debug'))

    log_level = logging.DEBUG if debug else logging.INFO
    logging.getLogger().setLevel(log_level)

    dir_manager_client = DirectoryManagerClient(api_base=arguments['--dir-manager'], default_protocol=Protocol.FTP)

    task = RotateTask(client_requestor=Client(arguments['--db-rest']), opv_directorymanager_client=dir_manager_client)
    task.run(options={"lotId": arguments['<id-lot>']})

if __name__ == "__main__":
    main()
