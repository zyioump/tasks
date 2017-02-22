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
# Description: Tile the Panorama

import logging
from path import Path
import json
import tempfile

logger = logging.getLogger(__name__)

from opv_tasks.const import Const
from .task import Task

class TilingTask(Task):
    """
    Tile the panorama
    """
    TILESIZE = "512"
    CUBESIZE = "0"
    QUALITY = "75"
    PNG = False

    def tile(self, pano_path):

        script_path = Path(__file__).dirname() / "../3rd/tile.py"

        with tempfile.TemporaryDirectory() as output_dirpath:
            output_dirpath = Path(output_dirpath) / "output"

            self._run_cli('python', [script_path,
                '--output', output_dirpath,
                '--tilesize', self.TILESIZE,
                '--cubesize', self.CUBESIZE,
                '--quality', self.QUALITY
                ]
                + (['--png'] if self.PNG else [])
                + [pano_path]
                )

            self.tile = self._client_requestor.Tile()

            with self._opv_directory_manager.Open() as (param_uuid, param_location):
                for loc in output_dirpath.glob("[0-9]*"):
                    loc.move(param_location)
                self.tile.param_location = param_uuid

            with self._opv_directory_manager.Open() as (fallback_uuid, fallback_location):
                (output_dirpath / "fallback").move(fallback_location)
                self.tile.fallback_path = fallback_uuid


            with open(output_dirpath / "config.json") as fp:
                tile_config = json.load(fp)["multiRes"]

                self.tile.extension = tile_config["extension"]
                self.tile.max_level = tile_config['maxLevel']
                self.tile.resolution = tile_config['tileResolution']
                self.tile.cube_resolution = tile_config['cubeResolution']

            self.tile.panorama = self.pano

            self.tile.save()



    def run(self, options={}):
        if "id" in options:
            self.pano = self._client_requestor.Panorama(options["id"])
            with self._opv_directory_manager.Open(self.pano.equirectangular_path) as (_, pano_dirpath):
                pano_path = Path(pano_dirpath) / Const.PANO_FILENAME

                self.tile(pano_path)

            return json.dumps({"id": self.tile.id})
