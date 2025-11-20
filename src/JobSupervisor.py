# coding=utf-8
# Copyright (C) 2018-2025 by dream-alpha
# License: GNU General Public License v3.0 (see LICENSE file for details)


from Components.Task import job_manager, JobManager
from .Debug import logger


instance = None


class JobSupervisor():

    def __init__(self):
        self.job_managers = {}
        self.job_managers["DEFAULT"] = job_manager

    @staticmethod
    def getInstance():
        global instance  # pylint: disable=global-statement
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
