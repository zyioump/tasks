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
# Description: Abstract class for representing task, you must redefine the run methods.

from path import Path
from opv_tasks.task import Task, TaskInvalidArgumentsException
from hsi import Panorama, ifstream, ofstream
from opv_api_client import ressources
from opv_tasks.const import Const

class InjectcpapnTask(Task):
    """
    Inject control points from a cp to an other.
    Yes it's not legit ;)
    """

    TASK_NAME = "injectcpapn"
    requiredArgsKeys = ["idCpFrom", "idCpTo", "apnList"]

    def fetchPanorama(self, project_file):
        """
        Return HSI panorama object from project_file.

        :param project_file: Path to projet file.
        :return: Panorama HSI.
        """
        ifs = ifstream(project_file)

        p = Panorama()
        p.readData(ifs)
        del ifs
        return p

    def huginPicNumber2Apnid(self, huginPicNo):
        """
        Associate hugin APN id to real APN number.

        :param huginPicNo: Hugin image id.
        :retrun: Real APN number ID.
        """
        return Const.CP_HUGIN_IMGID_2_APNID[huginPicNo]

    def removeCpForApnIds(self, cps, apnList):
        """
        Remove cp in cps for APN listed in apnList.

        :param cps: A **list** of cp.
        :param apnList: List of APN to be removed.
        :return: The list with removed cp.
        """
        resultCps = []
        for cp in cps:
            apnNo1 = self.huginPicNumber2Apnid(cp.image1Nr)
            apnNo2 = self.huginPicNumber2Apnid(cp.image2Nr)
            if apnNo1 in apnList or apnNo2 in apnList:
                self.logger.debug("Remove CP concerning : " + str(apnNo1) + " / " + str(apnNo2))
            else:
                resultCps.append(cp)
        return resultCps

    def injectCp(self, cpSource, cpDest, apnList, deleteAllCp=False):
        """
        Inject control points of apn listed in apnList from cpSource to cpDest.

        :param cpSource: Source for control points.
        :param cpDest: Destination for control points.
        :param apnList: List of APN where we inject points.
        :param deleteAllCp: remove all CP from dest for listed apnList.
        """

        with self._opv_directory_manager.Open(cpSource.pto_dir) as (_, ptoSourceDir):
            self.logger.debug("Source project file opened : " + cpSource.pto_dir)
            with self._opv_directory_manager.Open(cpDest.pto_dir) as (_, ptoDestDir):
                self.logger.debug("Dest project file opened : " + cpDest.pto_dir)
                panoSource = self.fetchPanorama(Path(ptoSourceDir) / Const.CP_PTO_FILENAME)
                panoDest = self.fetchPanorama(Path(ptoDestDir) / Const.CP_PTO_FILENAME)

                cpsSource = list(panoSource.getCtrlPoints())
                cpsDest = list(panoSource.getCtrlPoints())

                self.logger.debug("Cp Dest length (before removed) : " + str(len(cpsDest)))

                # If user also want to remove them
                if deleteAllCp:
                    cpsDest = self.removeCpForApnIds(cpsDest, apnList)

                self.logger.debug("Cp Dest length (after removed) : " + str(len(cpsDest)))

                for cpS in cpsSource:
                    apnNo1 = self.huginPicNumber2Apnid(cpS.image1Nr)
                    apnNo2 = self.huginPicNumber2Apnid(cpS.image2Nr)
                    # self.logger.debug("apnNo1: " + str(apnNo1) + " - apnNo2:" + str(apnNo2))
                    # self.logger.debug("apnList: " + str(apnList))
                    if apnNo1 in apnList or apnNo2 in apnList:
                        self.logger.debug("Injecting CP concerning : " + str(apnNo1) + " / " + str(apnNo2))
                        cpsDest.append(cpS)

                self.logger.debug("Cp Dest length : " + str(len(cpsDest)))

                # Saving added control points
                self.logger.debug("Saving dest project file : " + cpDest.pto_dir)
                panoDest.setCtrlPoints(tuple(cpsDest))
                ofs = ofstream(Path(ptoDestDir) / Const.CP_PTO_FILENAME)
                panoDest.writeData(ofs)
                del ofs

                # Setting optimized to false
                cpDest.optimized = False
                cpDest.save()

    def runWithExceptions(self, options={}):
        """
        Transfer control point linking to a specific apn number for a project file cpFrom to cpTo.

        :param options: { "idCpFrom"; {"id_cp": IDFrom, "id_malette": IDFrom}, "idCpTo"; {"id_cp": IDTo, "id_malette": IDTo}, "apnList": [0, 2], "deleteAllCp": True }
        :return: {"id_cp": IDTo, "id_malette": IDTo}
        """
        self.checkArgs(options)

        if "id_cp" in options["idCpFrom"] and "id_malette" in options["idCpFrom"] \
                and "id_cp" in options["idCpTo"] and"id_malette" in options["idCpTo"]:
                self.cpFrom = self._client_requestor.make(ressources.Cp, options["idCpFrom"]["id_cp"], options["idCpFrom"]["id_malette"])
                self.cpTo = self._client_requestor.make(ressources.Cp, options["idCpTo"]["id_cp"], options["idCpTo"]["id_malette"])

                deleteAllCp = True if "deleteAllCp" in options and options["deleteAllCp"] else False

                self.injectCp(cpSource=self.cpFrom, cpDest=self.cpTo, apnList=options["apnList"], deleteAllCp=deleteAllCp)

                return options["idCpTo"]
        else:
            raise TaskInvalidArgumentsException(requiredArguements=self.requiredArgsKeys, invalidArguments=['subArguments'])  # TODO improve it
