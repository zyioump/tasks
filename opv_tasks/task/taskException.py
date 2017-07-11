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
# Description: Abstract class for representing a task exception.task.

from opv_tasks.task import TaskStatusCode

class TaskException(Exception):
    """
    Abstract layer to represente a TaskException, might evolve in the futur.
    """

    def getErrorMessage(self):
        """
        Error message use in TaskReturn, might be overrided.

        :return: An error message string.
        """
        raise self.__str__()

    def getStatusCode(self):
        """
        Status code, if you what to use specific status code.

        :return: A TaskStatusCode.
        """
        return TaskStatusCode.ERROR
