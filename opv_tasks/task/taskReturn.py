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
# Description: Data returned by a task.

import json

from opv_tasks.task import TaskStatusCode

class TaskReturn:
    """
     Represent return value of a task.
    """

    def __init__(self, taskName=None, jsonStr=None, statusCode=TaskStatusCode.SUCCESS, inputData={}, outputData={}, error=None):
        """
        Init TaskReturn with values or from json string.
        """
        if jsonStr is not None:
            self.fromJSON(jsonStr)
        else:
            self.statusCode = statusCode    # Return status code
            self.taskName = taskName        # Task name (string)
            self.error = error              # Error string message
            self.inputData = inputData      # Task input data dict
            self.outputData = outputData    # Task output (returned) data dict

    def isSuccess(self):
        return self.statusCode == TaskStatusCode.SUCCESS

    def toJSON(self):
        """ Convert task return to JSON"""
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def fromJSON(self, jsonString):
        """ Map TaskReturn from JSON """
        data = json.loads(jsonString)
        self.statusCode = data['statusCode']
        self.taskName = data['taskName']
        self.error = data['error']
        self.inputData = data['inputData']
        self.outputData = data['outputData']
