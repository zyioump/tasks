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

from opv_tasks.task import TaskReturn, TaskStatusCode, TaskException

class Task:
    """An abstract class, you must redefine the run method."""

    TASK_NAME = None            # TaskName should be set in the implementation
    requiredArgsKeys = None     # Required arguments key for checkArgs

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

    def checkArgs(self, options):
        """
        Check the arguments/options given to a task.run.
        This method is based on a list of required argument self.requiredArgsKeys which should be defined by the implementation class.

        :param options: Actual option to be checked.
        :raise TaskInvalidArgumentsException: Exeption when some arguments are missing.
        """
        missingArguments = []
        if self.requiredArgsKeys is not None:
            for k in self.requiredArgsKeys:
                if not(k in options):
                    missingArguments.append(k)

        if len(missingArguments) > 0:
            raise TaskInvalidArgumentsException(requiredArguements=self.requiredArgsKeys, invalidArguments=missingArguments)

        return True

    def runWithExceptions(self, inputData):
        """
        Run task that doesn't use TaskReturn but might raise some exceptions.
        The exceptions are TaskExceptions and will be encapsulated into.
        We should implement this method or overide the run method.

        :param inputData: Task input data.
        :return: Shloud return Task ouput data.
        """
        raise NotImplementedError

    def run(self, options={}):
        """
        Run the task, will trap all TaskException into a TaskReturn object.
        If you don't like the way we handle these exception just overidde this method.

        :param options: Options to use
        :return: TaskReturn
        :raise
        """

        if self.TASK_NAME is None:
            raise NotImplemented("TASK_NAME is not implemented in task implementation.")

        taskReturn = TaskReturn(taskName=self.TASK_NAME)

        # Running task and handeling exceptions
        try:
            taskOutput = self.runWithExceptions(options=options)
            taskReturn.outputData = taskOutput
            taskReturn.statusCode = TaskStatusCode.SUCCESS
        except TaskException as taskException:
            taskReturn.error = taskException.getErrorMessage()
            taskReturn.statusCode = TaskStatusCode.ERROR

        return taskReturn

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

class TaskInvalidArgumentsException(TaskException):
    """ Raised when some arguments/options are missing or invalid"""

    def __init__(self, requiredArguements=[], invalidArguments=[]):
        """
        Init exception with requiredArguments and invalidArguments.

        :param requiredArguments:   List of all the requiredArguments.
        :param invalidArguments:    List of all the invalidArguments.
        """
        self.requiredArguments = requiredArguements
        self.invalidArguments = invalidArguments

    def getErrorMessage(self):
        return "Invalid Arguments, requiredArguments are the following : " + repr(self.requiredArguments) + \
            " these arguments are invalid or missing : " + str(self.invalidArguments)
