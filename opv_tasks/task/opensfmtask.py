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
from collections import defaultdict
import uuid
import math
import json

from path import Path
from opv_api_client import ressources

from opv_tasks.task import Task
from opv_tasks.const import Const

class OpensfmTask(Task):
    """create tracks in DB"""

    DATADIR = Path("~/opv/OpenSfM-data").expanduser()

    default_config_yaml = """
processes: 8                  # Number of threads to use
    """

    def __init__(self, *args, **kwargs):
        self.reconstruction_json = None
        self.folder_dirname = None
        self.folder_data_dir = None
        self.filenames = {}
        self.panos = None
        self.campaign = None

        super().__init__(*args, **kwargs)

    def find_pano(self):
        """List all panos from self.campaign"""
        return [pano for lots in self.campaign.lots for cps in lots.cps for pano in cps.panorama]

    def make_folder_datapath(self):
        """Make an unique path in DATADIR for datas"""
        self.folder_dirname = (self.campaign.name + '-' + str(uuid.uuid4()))
        self.folder_data_dir = self.DATADIR / self.folder_dirname

    def make_open_sfm_datadir(self):
        """populate the opensfm data path with imgs and config.yaml"""
        self.make_folder_datapath()
        img_dir = self.folder_data_dir / "images"
        config_yaml = self.folder_data_dir / "config.yaml"

        self.folder_data_dir.mkdir_p()

        with open(config_yaml, "x") as configf:
            configf.write(self.default_config_yaml)

        img_dir.mkdir_p()

        can_harlink = True

        # Copy or hardlink img to images sub dir
        for pano in self.panos:
            if not pano.is_photosphere:
                continue
            with self._opv_directory_manager.Open(
                pano.equirectangular_path) as (_, picture_dir):

                picture_dir = Path(picture_dir)
                picture_path = picture_dir / Const.PANO_FILENAME

                img_filename = self.make_filename(pano)

                self.filenames[img_filename] = pano # associate filename with panos

                dest_picture_path = img_dir / img_filename

                if can_harlink:
                    try:
                        picture_path.link(dest_picture_path)
                    except OSError:
                        can_harlink = False
                if not can_harlink:
                    picture_path.copy(dest_picture_path)

    @staticmethod
    def make_filename(pano):
        """
        Allow to get an unique filename for a pano.
        The filename is always the same when pano is the same
        """
        return "-".join(map(str, pano.id.values())) + Path(Const.PANO_FILENAME).ext

    def opensfm(self, task):
        """A wrapper that allow to run opensfm"""
        self._run_cli("docker",
                      [
                          "run",
                          "-e", "command={}".format(task),
                          "-e", "folderData={}".format(self.folder_dirname),
                          "--volumes-from", "opensfmstore",
                          "opv/opensfm-dev"
                      ]
                     )

    def run_opensfm(self):
        """Here, we will launch opensfm to get what we need and append data when needed"""
        self.opensfm("extract_metadata")

        exif_dir = self.folder_data_dir / "exif"
        for metadata_file in exif_dir.files():
            self.complete_metadata(metadata_file)

        self.opensfm("detect_features")
        self.opensfm("match_features")
        self.opensfm("create_tracks")

        self.opensfm("reconstruct")
        self.opensfm("mesh")

    def complete_metadata(self, filename):
        """Add data (gps_pos) to metadata extracted by opensfm from exifs"""
        with open(filename, "r") as metadataf:
            j = json.load(metadataf)

        key = filename.basename().splitext()[0] # get the part id.jpg of path
        pano = self.filenames[key]
        sensors = pano.cp.lot.sensors

        # TODO: capture_time
        lat, lng, alt = sensors.gps_pos["coordinates"]
        j['gps']['latitude'] = lat
        j['gps']['longitude'] = lng
        j['gps']['altitude'] = alt

        with open(filename, "w") as metadataf:
            json.dump(j, metadataf)

    def cleanup(self):
        """Remove all data used"""
        self.folder_data_dir.rm_tree()

    def add_tracks_to_db(self):
        """Allow to append created tracks to db to keep trace of them"""
        for pano_from, panos_to  in self.get_tracks().items():

            for pano_to, rot in panos_to:
                track_edge = self._client_requestor.make(ressources.TrackEdge)
                track_edge.id_malette = pano_from.id_malette
                track_edge.panorama_from = pano_from
                track_edge.panorama_to = pano_to
                track_edge.rotx, track_edge.roty, track_edge.rotz = rot
                track_edge.create()


    def get_tracks(self):
        """Get tracks from data Computed by opensfm and transform it in a move usable way"""
        csv = []
        with open(self.folder_data_dir / "tracks.csv") as trackf:
            for row in trackf.readlines():
                csv.append(row.strip().split('\t'))

        panos_track = defaultdict(set) # list of track linked to a pano
        tracks_pano = defaultdict(set) # list of panos linked to a track

        for img, track, *_ in csv: # We do not care about the rest of data
            pano = self.filenames[img] # get pano from filename
            tracks_pano[track].add(pano)
            panos_track[pano].add(track)

        tracks = defaultdict(set)
        for pano, track in panos_track.items():
            for track_id in track:
                tracks[pano] |= tracks_pano[track_id]

        track_and_direc = {}

        for pano1, panos in tracks.items():
            track_and_direc[pano1] = set()
            for pano2 in panos:
                coord1, coord2 = self.get_im_pos_rot(pano1), self.get_im_pos_rot(pano2)

                rot = self.get_direc(coord1, coord2)
                if rot:
                    track_and_direc[pano1].add((pano2, rot))

        return track_and_direc

    def get_im_pos_rot(self, pano):
        """Get gps_position and rotation conputed by opensfm for a pano"""
        img = self.make_filename(pano)

        if self.reconstruction_json is None:
            with open(self.folder_data_dir / "reconstruction.json") as reconstructionf:
                self.reconstruction_json = json.load(reconstructionf)

        for obj in self.reconstruction_json:
            try:
                img_json = obj["shots"][img]
            except KeyError:
                continue
            break

        pos = img_json["gps_position"]
        rot = img_json["rotation"]

        return pos, rot

    @staticmethod
    def get_direc(coord1, coord2):
        """Compute necessary angles needed to place a point to get from A(1) to B(2)"""
        pos1, rot1 = coord1
        pos2, _ = coord2

        vect = (
            pos1[0] - pos2[0],
            pos1[1] - pos2[1],
            pos1[2] - pos2[2]
            )

        # distance AB
        dist = math.sqrt(sum(map(lambda x: x**2, vect)))

        if dist == 0: # coord1 ~= coord2
            return

        roll = math.acos(vect[0]/dist) - rot1[0]
        pitch = math.acos(vect[1]/dist) - rot1[1]
        yaw = math.acos(vect[2]/dist) - rot1[2]

        return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)

    def run(self, options=None):
        if not options:
            options = dict()

        if "id" in options:
            self.campaign = self._client_requestor.make(ressources.Campaign, *options["id"])

            self.panos = self.find_pano()
            self.make_open_sfm_datadir()
            self.run_opensfm()
            self.add_tracks_to_db()

            # self.cleanup()

            # return json.dumps({"id": self.cp.id})
