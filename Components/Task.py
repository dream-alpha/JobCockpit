# pylint: disable-all

import os
from enigma import eConsoleAppContainer
from Tools.CList import CList
from Tools import Notifications


Notifications.notificationQueue.registerDomain("JobManager", _("Job Manager"), Notifications.ICON_DEFAULT)  # pylint: disable=E0602


class Job(object):
	NOT_STARTED, IN_PROGRESS, FINISHED, FAILED = range(4)

	def __init__(self, name):
		self.tasks = []
		self.resident_tasks = []
		self.workspace = "/tmp"
		self.current_task = 0
		self.callback = None
		self.name = name
		self.finished = False
		self.end = 100
		self.__progress = 0
		self.weightScale = 1
		self.afterEvent = None
		self.state_changed = CList()
		self.status = self.NOT_STARTED

	# description is a dict
	def fromDescription(self, description):
		pass

	def createDescription(self):
		return None

	def getProgress(self):
		# if self.current_task == len(self.tasks):
			# return self.end
		# t = self.tasks[self.current_task]
		# jobprogress = t.weighting * t.progress / float(t.end) + sum([task.weighting for task in self.tasks[:self.current_task]])
		jobprogress = sum([task.weighting * task.progress / float(task.end) for task in self.tasks])
		progress = int(jobprogress * self.weightScale)
		print("JOB: getProgress: progress: %s" % progress)
		return int(jobprogress * self.weightScale)

	progress = property(getProgress)

	def getStatustext(self):
		return {self.NOT_STARTED: _("Waiting"), self.IN_PROGRESS: _("In Progress"), self.FINISHED: _("Finished"), self.FAILED: _("Failed")}[self.status]  # pylint: disable=E0602

	def task_progress_changed_CB(self):
		self.state_changed()

	def addTask(self, task):
		print("JOB: addTask: %s" % task)
		task.job = self
		task.task_progress_changed = self.task_progress_changed_CB
		self.tasks.append(task)

	def start(self, callback):
		print("JOB: start: %s" % callback)
		assert self.callback is None
		self.callback = callback
		self.restart()

	def restart(self):
		print("JOB: restart")
		self.status = self.IN_PROGRESS
		self.state_changed()
		self.runNext()
		sumTaskWeightings = sum([t.weighting for t in self.tasks]) or 1
		self.weightScale = self.end / float(sumTaskWeightings)

	def runNext(self):
		print("JOB: runNext: current_task: %s, tasks: %s" % (self.current_task, self.tasks))
		if self.current_task == len(self.tasks):
			if len(self.resident_tasks) == 0:
				self.status = self.FINISHED
				self.state_changed()
				self.callback(self, None, [])
				self.callback = None
			else:
				print("JOB: still waiting for %d resident task(s) %s to finish" % (len(self.resident_tasks), str(self.resident_tasks)))
		else:
			print("JOB: current_task: %s" % self.current_task)
			print("JOB: tasks: %s" % self.tasks)
			self.tasks[self.current_task].run(self.taskCallback)
			self.state_changed()

	def taskCallback(self, task, res, stay_resident=False):
		print("JOB: taskCallback: task: %s, res: %s, stay_residents: %s" % (task, res, stay_resident))
		cb_idx = self.tasks.index(task)
		if stay_resident:
			if cb_idx not in self.resident_tasks:
				self.resident_tasks.append(self.current_task)
				print("JOB: task going resident:", task)
			else:
				print("JOB: task keeps staying resident:", task)
				return
		if len(res) > 0:
			print("JOB: >>> Error:", res)
			self.status = self.FAILED
			self.state_changed()
			self.callback(self, task, res)
		if cb_idx != self.current_task:
			if cb_idx in self.resident_tasks:
				print("JOB: resident task finished:", task)
				self.resident_tasks.remove(cb_idx)
		if res == []:
			self.state_changed()
			self.current_task += 1
			self.runNext()

	def retry(self):
		assert self.status == self.FAILED
		self.restart()

	def abort(self, *args):
		print("JOB: abort")
		if self.current_task < len(self.tasks):
			self.tasks[self.current_task].abort(*args)
		for i in self.resident_tasks:
			self.tasks[i].abort(*args)

	def cancel(self, *args):
		print("JOB: cancel")
		self.abort(*args)

	def remove(self, callback):
		print("JOB: remove: callback: %s" % callback)
		if self.status == self.IN_PROGRESS:
			self.abort()
		else:
			callback(self, None, [])


class Task(object):
	def __init__(self, job, name):
		self.name = name
		self.immediate_preconditions = []
		self.global_preconditions = []
		self.postconditions = []
		self.returncode = None
		self.initial_input = None
		self.job = None
		self.end = 100
		self.weighting = 100
		self.__progress = 0
		self.cmd = None
		self.cwd = "/tmp"
		self.args = []
		self.cmdline = None
		self.task_progress_changed = None
		self.output_line = ""
		job.addTask(self)
		self.container = None

	def setCommandline(self, cmd, args):
		self.cmd = cmd
		self.args = args

	def setTool(self, tool):
		self.cmd = tool
		self.args = [tool]
		self.global_preconditions.append(ToolExistsPrecondition())
		self.postconditions.append(ReturncodePostcondition())

	def setCmdline(self, cmdline):
		self.cmdline = cmdline

	def checkPreconditions(self, immediate=False):
		not_met = []
		if immediate:
			preconditions = self.immediate_preconditions
		else:
			preconditions = self.global_preconditions
		for precondition in preconditions:
			if not precondition.check(self):
				not_met.append(precondition)
		return not_met

	def run(self, callback):
		failed_preconditions = self.checkPreconditions(True) + self.checkPreconditions(False)
		if len(failed_preconditions) > 0:
			callback(self, failed_preconditions)
			return
		self.prepare()

		self.callback = callback
		self.container = eConsoleAppContainer()
		self.appClosed_conn = self.container.appClosed.connect(self.processFinished)
		self.stdoutAvail_conn = self.container.stdoutAvail.connect(self.processStdout)
		self.stderrAvail_conn = self.container.stderrAvail.connect(self.processStderr)

		if self.cwd is not None:
			self.container.setCWD(self.cwd)

		if not self.cmd and self.cmdline:
			print("TASK: execute:", self.container.execute(self.cmdline), self.cmdline)
		else:
			assert self.cmd is not None
			assert len(self.args) >= 1
			print("TASK: execute:", self.container.execute(self.cmd, *self.args), ' '.join(self.args))
		if self.initial_input:
			self.writeInput(self.initial_input)

	def prepare(self):
		pass

	def cleanup(self, failed):
		pass

	def processStdout(self, data):
		self.processOutput(data)

	def processStderr(self, data):
		self.processOutput(data)

	def processOutput(self, data):
		self.output_line += data
		while True:
			i = self.output_line.find('\n')
			if i == -1:
				break
			self.processOutputLine(self.output_line[:i + 1])
			self.output_line = self.output_line[i + 1:]

	def processOutputLine(self, line):
		pass

	def processFinished(self, returncode):
		self.returncode = returncode
		self.finish()

	def abort(self):
		if self.container:
			self.container.kill()
		self.finish(aborted=True)

	def finish(self, aborted=False):
		self.afterRun()
		not_met = []
		if aborted:
			not_met.append(AbortedPostcondition())
		else:
			for postcondition in self.postconditions:
				if not postcondition.check(self):
					not_met.append(postcondition)
		self.cleanup(not_met)
		self.callback(self, not_met)

	def afterRun(self):
		pass

	def writeInput(self, ainput):
		self.container.write(ainput)

	def getProgress(self):
		print("TASK: getProgress: __progress: %s" % self.__progress)
		return self.__progress

	def setProgress(self, progress):
		print("TASK: setProgress: progress: %s" % progress)
		if progress > self.end:
			progress = self.end
		if progress < 0:
			progress = 0
		self.__progress = progress
		if self.task_progress_changed:
			self.task_progress_changed()  # pylint: disable=E1102
		print("TASK: setProgress: __progress: %s" % self.__progress)

	progress = property(getProgress, setProgress)


# The jobmanager will execute multiple jobs, each after another.
# later, it will also support suspending jobs (and continuing them after reboot etc)
# It also supports a notification when some error occured, and possibly a retry.


class JobManager:
	def __init__(self, domain="JobManager"):
		self.active_jobs = []
		self.successfull_jobs = []
		self.failed_jobs = []
		self.job_classes = []
		self.in_background = False
		self.active_job = None
		self.domain = domain

	def AddJob(self, job):
		self.active_jobs.append(job)
		self.kick()

	def AbortJob(self, job, *args):
		if job.status == Job.IN_PROGRESS:
			job.abort(*args)

	def RemoveJob(self, job):
		if job.status == Job.NOT_STARTED:
			if job in self.active_jobs:
				self.active_jobs.remove(job)
		elif job.status == Job.FINISHED:
			if job in self.successfull_jobs:
				self.successfull_jobs.remove(job)
		elif job.status == Job.FAILED:
			if job in self.failed_jobs:
				self.failed_jobs.remove(job)

	def CleanupJobs(self):
		self.successfull_jobs = []
		self.failed_jobs = []

	def kick(self):
		if self.active_job is None:
			if len(self.active_jobs) > 0:
				self.active_job = self.active_jobs.pop(0)
				self.active_job.start(self.jobDone)

	def jobDone(self, job, task, problems):
		print("JOBMGR: job", job, "completed with", problems, "in", task)
		if self.in_background:
			from Screens.TaskView import JobView  # pylint: disable=C0415
			self.in_background = False
			Notifications.AddNotification(JobView, self.active_job, domain=self.domain)
		if problems:
			from Screens.MessageBox import MessageBox  # pylint: disable=C0415
			if problems[0].RECOVERABLE:
				Notifications.AddNotificationWithCallback(self.errorCB, MessageBox, _("Error: %s\nRetry?") % (problems[0].getErrorMessage(task)), domain=self.domain)  # pylint: disable=E0602
			else:
				Notifications.AddNotification(MessageBox, _("Error") + (': %s') % (problems[0].getErrorMessage(task)), type=MessageBox.TYPE_ERROR, domain=self.domain)  # pylint: disable=E0602
				self.errorCB(False)
			if hasattr(self.active_job, "keep") and self.active_job.keep:
				self.failed_jobs.append(self.active_job)
			return
		if hasattr(self.active_job, "keep") and self.active_job.keep:
			self.successfull_jobs.append(self.active_job)

		self.active_job = None
		self.kick()

	def errorCB(self, answer):
		if answer:
			print("JOBMGR: retrying job")
			self.active_job.retry()
		else:
			print("JOBMGR: not retrying job.")
			self.failed_jobs.append(self.active_job)
			self.active_job = None
			self.kick()

	def getPendingJobs(self):
		jobs = []
		if self.active_job:
			jobs.append(self.active_job)
		jobs += self.active_jobs
		return jobs

	def getSuccessfullJobs(self):
		return self.successfull_jobs

	def getFailedJobs(self):
		return self.failed_jobs


# some examples:
# class PartitionExistsPostcondition:
# 	def __init__(self, device):
# 		self.device = device
#
# 	def check(self, task):
# 		import os
# 		return os.access(self.device + "part1", os.F_OK)
#
# class CreatePartitionTask(Task):
# 	def __init__(self, device):
# 		Task.__init__(self, _("Create Partition"))
# 		self.device = device
# 		self.setTool("/sbin/sfdisk")
# 		self.args += ["-f", self.device + "disc"]
# 		self.initial_input = "0,\n;\n;\n;\ny\n"
# 		self.postconditions.append(PartitionExistsPostcondition(self.device))
#
# class CreateFilesystemTask(Task):
# 	def __init__(self, device, partition = 1, largefile = True):
# 		Task.__init__(self, _("Create Filesystem"))
# 		self.setTool("/sbin/mkfs.ext")
# 		if largefile:
# 			self.args += ["-T", "largefile"]
# 		self.args.append("-m0")
# 		self.args.append(device + "part%d" % partition)
#
# class FilesystemMountTask(Task):
# 	def __init__(self, device, partition = 1, filesystem = "ext3"):
# 		Task.__init__(self, _("Mounting Filesystem"))
# 		self.setTool("/bin/mount")
# 		if filesystem is not None:
# 			self.args += ["-t", filesystem]
# 		self.args.append(device + "part%d" % partition)


class Condition:
	RECOVERABLE = False

	def getErrorMessage(self, task):
		return _("An unknown error occured!") + " (%s @ task %s)" % (self.__class__.__name__, task.__class__.__name__)  # pylint: disable=E0602


class DiskspacePrecondition(Condition):
	def __init__(self, diskspace_required):
		self.diskspace_required = diskspace_required
		self.diskspace_available = 0

	def check(self, task):
		try:
			s = os.statvfs(task.job.workspace)
			self.diskspace_available = s.f_bsize * s.f_bavail
			return self.diskspace_available >= self.diskspace_required
		except OSError:
			return False

	def getErrorMessage(self, task):
		return _("Not enough diskspace. Please free up some diskspace and try again. (%d MB required, %d MB available)") % (self.diskspace_required / 1024 / 1024, self.diskspace_available / 1024 / 1024)  # pylint: disable=E0602


class ToolExistsPrecondition(Condition):
	def check(self, task):
		if task.cmd[0] == '/':
			self.realpath = task.cmd
			print("[Task.py][ToolExistsPrecondition] WARNING: usage of absolute paths for tasks should be avoided!")
			return os.access(self.realpath, os.X_OK)
		self.realpath = task.cmd
		path = os.environ.get('PATH', '').split(os.pathsep)
		path.append(task.cwd + '/')
		absolutes = filter(lambda file: os.access(file, os.X_OK), map(lambda directory, file=task.cmd: os.path.join(directory, file), path))
		if len(absolutes) > 0:
			self.realpath = task.cmd[0]
			return True
		return False

	def getErrorMessage(self, task):
		return _("A required tool (%s) was not found.") % (self.realpath)  # pylint: disable=E0602


class AbortedPostcondition(Condition):
	def getErrorMessage(self, task):
		return "Cancelled upon user request"


class ReturncodePostcondition(Condition):
	def check(self, task):
		return task.returncode == 0


# class HDDInitJob(Job):
# 	def __init__(self, device):
# 		Job.__init__(self, _("Initialize Harddisk"))
# 		self.device = device
# 		self.fromDescription(self.createDescription())
#
# 	def fromDescription(self, description):
# 		self.device = description["device"]
# 		self.addTask(CreatePartitionTask(self.device))
# 		self.addTask(CreateFilesystemTask(self.device))
# 		self.addTask(FilesystemMountTask(self.device))
#
# 	def createDescription(self):
# 		return {"device": self.device}

job_manager = JobManager()
