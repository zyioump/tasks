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

# Contributors: Christophe NOUCHET <christophe.nouchet@openpathview.fr>
# Email: team@openpathview.fr
# Description: Abstract class for representing task, you must redefine the run methods.

import subprocess
import logging
import threading

class Task:
    """An abstract class, you must redefine the run method."""

    def __init__(self, client_requestor, opv_directorymanager_client):
        """
        Create a task.

        :param client_requestor: the client requestor to use for the task
        :param opv_directorymanager_client: The client directory manager to use
        """
        self._client_requestor = client_requestor
        self._opv_directory_manager = opv_directorymanager_client

        logger_name = "opv_task." + self.__class__.__name__
        shell_logger_name = logger_name + '.shell'

        self.logger = logging.getLogger(logger_name)  # Used in subclasses
        self.shell_logger = logging.getLogger(shell_logger_name)  # Used when you use _run_cli

    def run(self, options={}):
        """
        Run the task.

        :param options: Options to use
        :return:
        :raise
        """
        raise NotImplementedError

    def _run_cli(self, cmd, args=[], stdout_level=logging.INFO, stderr_level=logging.WARNING):
        """
        Run a command.

        :param cmd: Command to use
        :param args: Args to pass to the command
        :param stdout_level: Level to use to log the stdout (INFO, DEBUG...) -> same as in the logging module
        :param stderr_level: Same as stdout_level, for stderr
        :return: return code of the cli
        """
        my_cmd = cmd if isinstance(cmd, list) else [cmd]
        my_args = args if isinstance(args, list) else [args]
        proc = subprocess.Popen(
            my_cmd + my_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        def log_output(handler, logger, level):
            for line in handler:
                logger.log(level, line.strip())

        # Use threads to log in the same time
        threading.Thread(target=log_output, args=[proc.stdout, self.shell_logger, stdout_level]).start()
        threading.Thread(target=log_output, args=[proc.stderr, self.shell_logger, stderr_level]).start()

        proc.wait()

        return proc.returncode
