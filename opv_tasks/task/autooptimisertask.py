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
# Description: Optimise CP geometrie.
""" Optimise CP (autooptimiser).

Usage:
    opv-task-autooptimiser <id-cp> [--db-rest=<str>] [--dir-manager=<str>] [--debug]
    opv-task-autooptimiser (-h | --help)

Options:
    -h --help                Show help.
    --db-rest=<str>          API rest server [default: http://localhost:5000]
    --dir-manager=<str>      API for directory manager [default: http://localhost:5001]
    --debug                  Debug mode.
"""

import os
import logging
import json
from path import Path
from shutil import copyfile
from docopt import docopt

from opv_tasks import Const
from opv_tasks.task import Task

class AutooptimiserTask(Task):
    """
        Optimise CP with cli autooptimiser.
    """

    AUTOOPTIMISER_OPTIONS = ["-a", "-m", "-l", "-s"]
    TMP_PTONAME = "opt.pto"
    TMP_OUTPUT = "out.pto"

    def optimise(self):
        """
        Optimise CP.
        """
        with self._opv_directory_manager.Open(self.cp.pto_dir) as (_, pto_dirpath):
            proj_pto = Path(pto_dirpath) / Const.CP_PTO_FILENAME

            with self._opv_directory_manager.Open(self.cp.lot.pictures_path) as (_, pictures_dir):
                local_tmp_pto = Path(pictures_dir) / self.TMP_PTONAME
                local_tmp_output = Path(pictures_dir) / self.TMP_OUTPUT

                logging.debug("Copy pto file " + proj_pto + " -> " + local_tmp_pto)
                copyfile(proj_pto, local_tmp_pto)

                options = list(self.AUTOOPTIMISER_OPTIONS)
                options.append("-o")
                options.append(local_tmp_output)  # Add output
                options.append(local_tmp_pto)  # Add input pto
                logging.debug("Running : " + "autooptimiser" + " ".join(options))
                input()
                self._run_cli("autooptimiser", options)
                input()
                self.cp.optimized = True

                os.rename(local_tmp_output, proj_pto)  # Copy back optimized verison
                os.unlink(local_tmp_pto)

    def run(self, options={}):
        if "cpId" in options:
            self.cp = self._client_requestor.Cp(options["cpId"])
            self.optimise()

            self.cp.save()

        return json.dumps({})


def main():
    from opv_directorymanagerclient import DirectoryManagerClient, Protocol
    from potion_client import Client

    arguments = docopt(__doc__)
    debug = bool(arguments.get('--debug'))

    log_level = logging.DEBUG if debug else logging.INFO
    logging.getLogger().setLevel(log_level)

    dir_manager_client = DirectoryManagerClient(api_base=arguments['--dir-manager'], default_protocol=Protocol.FTP)

    task = AutooptimiserTask(client_requestor=Client(arguments['--db-rest']), opv_directorymanager_client=dir_manager_client)
    task.run(options={"cpId": arguments['<id-cp>']})


if __name__ == "__main__":
    main()
