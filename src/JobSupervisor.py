# coding=utf-8
#
# Copyright (C) 2018-2025 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For more information on the GNU General Public License see:
# <http://www.gnu.org/licenses/>.


from Components.Task import job_manager, JobManager
from .Debug import logger


instance = None


class JobSupervisor():

    def __init__(self):
        self.job_managers = {}
        self.job_managers["DEFAULT"] = job_manager

    @staticmethod
    def getInstance():
        global instance
        if instance is None:
            instance = JobSupervisor()
        return instance

    def getJobManager(self, plugin_id):
        logger.info("plugin_id: %s", plugin_id)
        if plugin_id not in self.job_managers:
            self.job_managers[plugin_id] = JobManager()
        return self.job_managers[plugin_id]

    def createJobTuples(self, plugin_id, jobs, as_tuples):
        job_tuples = []
        if as_tuples:
            for job in jobs:
                job_tuples.append((plugin_id, job))
        else:
            job_tuples = jobs
        return job_tuples

    def getJobManagers(self, plugin_id=""):
        job_managers = {}
        if plugin_id:
            if self.job_managers.get(plugin_id, ""):
                job_managers = {
                    plugin_id: self.job_managers.get(plugin_id, "")}
        else:
            job_managers = self.job_managers
        return job_managers

    def getPendingJobs(self, plugin_id="", as_tuples=False):
        jobs = []
        for plugin, manager in self.getJobManagers(plugin_id).items():
            jobs += self.createJobTuples(plugin,
                                         manager.getPendingJobs(), as_tuples)
        return jobs

    def getFailedJobs(self, plugin_id="", as_tuples=False):
        jobs = []
        for plugin, manager in self.getJobManagers(plugin_id).items():
            jobs += self.createJobTuples(plugin,
                                         manager.getFailedJobs(), as_tuples)
        return jobs

    def getSuccessfullJobs(self, plugin_id="", as_tuples=False):
        jobs = []
        for plugin, manager in self.getJobManagers(plugin_id).items():
            jobs += self.createJobTuples(plugin,
                                         manager.getSuccessfullJobs(), as_tuples)
        return jobs
