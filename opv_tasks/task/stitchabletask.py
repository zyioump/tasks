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
# Description: Set in db isStichable if needed

from hsi import Panorama, ifstream
import sys
import logging

logger = logging.getLogger(__name__)

from .task import Task

class StitchableTask(Task):
    """
    Set in db isStichable if needed
    """
    def find_pto(self):
        return pto_file

    def stichable(self):
        ifs = ifstream(self.find_pto())

        p = Panorama()
        p.readData(ifs)

        cpv = p.getCtrlPoints()
        picLinkNb = [0 for x in range(6)]
        distSum = 0
        nbPoints = 0

        for cp in cpv:
            picLinkNb[cp.image1Nr] += 1
            picLinkNb[cp.image2Nr] += 1
            nbPoints += 1
        minLinksNeeded = 4

        isStitchable = all(x > minLinksNeeded for x in picLinkNb)

        self.cp.nb_cp = nbPoints
        self.cp.stichable = isStichable

    def run(self, options={}):
        if "lotId" in options:
            self.cp = self._client_requestor.Cp(options["lotId"])
            self.stichable()
            return json.dumps({"lotId": self.cp.id})
