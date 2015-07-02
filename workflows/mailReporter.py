#!/usr/bin/env python3

#####################################################################################################################
#										Mail Reporter Workflow Factory												#
#####################################################################################################################
#																Author: Manuel Bernal Llinares <mbdebian@gmail.com>	#
#####################################################################################################################
""" This factory creates Runners that will e-mail log or report files, or both of them
"""

# Running as part of the Workflow Engine ############################################################################
if not __name__ == "__main__":
	import configManager
	from exceptions import WorkflowRunnerException
	from workflows.workflowRunner import WorkflowRunner
	from workflows.workflowRunner import WfConfManager
	from workflows.Synchronization import *
# END of running as part of the Workflow Engine #####################################################################

# Modules from the system ###########################################################################################
import os
# END of Modules from the system ####################################################################################

# Abstract Factory Interface ########################################################################################
_runnerIdCounter = 0
def createWorkflowRunner(configFileName):
	""" It creates an instance of the Workflow runner implemented in this module, and it returns it back to the
	calling client
	"""
	global _runnerIdCounter
	runner = MyWorkflowRunner(configFileName, _runnerIdCounter)
	_runnerIdCounter += 1
	return runner
# Make the factory thread safe
synchronized('createWorkflowRunner')
# END of Abstract Factory Interface #################################################################################

class MyCustomException(Exception):
	def __init__(self, value):
		Exception.__init__(self)
		self.value = value
	def __str__(self):
		return repr(self.value)


# Support the Abstract Factory Product ##############################################################################
class ConfManager(WfConfManager):
	def __init__(self, configFileName, director):
		WfConfManager.__init__(self, configFileName, director)

	def isAttachLogFiles(self):
		key = "attachLogFiles"
		if self._getValueForKey(key) == "True":
			return True
		else:
			return False

	def isAttachReportFiles(self):
		key = "attachReportFiles"
		if self._getValueForKey(key) == "True":
			return True
		else:
			return False

	def getMailRecipient(self):
		key = "mailRecipient"
		return self._getValueForKey(key)

	def getMailServerConfigFilePath(self):
		key = "mailServerConfigFile"
		return os.path.abspath(configManager.getManager().getConfigFolder(), self._getValueForKey(key))

# END of Support the Abstract Factory Product #######################################################################


# Abstract Factory Product ##########################################################################################
class MyWorkflowRunner(WorkflowRunner):
	""" This is a template for the user to create its own workflows
	"""
	def __init__(self, configFileName, runnerId = 0):
		super(MyWorkflowRunner, self).__init__()
		self.__runnerId = runnerId
		self.__runnerIdName = __name__ + "-" + str(runnerId)
		self.__logger = configManager.getManager().createLogger(self.__runnerIdName)
		self.__reporter = configManager.getManager().createReporter(self.__runnerIdName + "_report")
		self.__logger.debug("Trying to load config file " + configFileName)
		self.__config = ConfManager(configFileName, self)
		self.__logger.debug("Workflow configuration file, " + self.__config.getConfigFilePath())
		self.__logger.debug("Runner created")

	def provides(self):
		return self.__config.getProvides()

	def requires(self):
		return self.__config.getRequires()

	def getLogger(self):
		return self.__logger

	def getReporter(self):
		return self.__reporter

	def getId(self):
		return self.__runnerId

	def getIdName(self):
		return self.__runnerIdName

	def _execute(self):
		""" This method is where your workflow does its job """
		self.__reporter.info("BEGIN --- workflow ID '" + self.__config.getWorkflowId() + "'")
		try:
			# TODO Place here the execution body of your runner
			pass
		except Exception as e:
			msg = "An error occurred while executing workflow ID '" + self.__config.getWorkflowId() + "', ERROR message:\n" + str(e)
			self.__reporter.error(msg)
			self.setError(msg)
			# We no longer raise an exception here, we use a result object to communicate the end of the process to
			# the calling object
			#raise MyCustomException(msg)
		finally:
			self.__reporter.info("END   --- workflow ID '" + self.__config.getWorkflowId() + "'")

# END of Abstract Factory Product ###################################################################################


# Unit tests ########################################################################################################
def unitTest():
	""" Unit Test method to run tests on this module when running stand alone """
	logger = configManager.getManager().getLogger()
	logger.debug("--- " * 4 + "Unit test running for '" + os.path.basename(__file__) + "'" + " ---" * 4)
	configFileName = "mailReporter-unit_test.conf.sample"
	logger.debug("Config file: " + configFileName)
	runner = createWorkflowRunner(configFileName)
	runner.execute()
# END of Unit tests #################################################################################################

# Unit testing environment detection and definition #################################################################
if __name__ == "__main__":
	import sys
	sys.stderr.writelines("This module is not designed to be run alone, please, test it using the Workflow Engine")
#####################################################################################################################

# END OF SCRIPT #####################################################################################################