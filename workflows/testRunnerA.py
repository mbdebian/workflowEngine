#!/usr/bin/env python3

#####################################################################################################################
#												Test Runner A														#
#####################################################################################################################
#																Author: Manuel Bernal Llinares <mbdebian@gmail.com>	#
#####################################################################################################################

# This workflow is a leaf in the WorkflowRunner hierarchy, included here for testing purposes




# Module init code ##################################################################################################
def _init():
	""" Initialization code for the module as part of the application """
	global _initializedEngine
	_initializedEngine = True
# END of Module init code ###########################################################################################


# Unit tests ########################################################################################################
def unitTest():
	""" Unit Test method to run tests on this module when running stand alone """
	pass
# END of Unit tests #################################################################################################


# Entry point #######################################################################################################
if __name__ == "__main__":
	# Set up here the unit test
	print("TestRunnerA - Preparing Unit Testing code...")
	# Set up things that we would normally get from the Application wide ConfigManager
	unitTest()
else:
	# We are running as part of the application
	import configManager
	from exceptions import WorkflowRunnerException
	from workflows.workflowRunner import WorkflowRunner
	from workflows.Synchronization import *
	_init()
# END of Entry point ################################################################################################




# Modules from the system ###########################################################################################
import os
import json
# END of Modules from the system ####################################################################################


# Abstract Factory Interface ########################################################################################
_runnerIdCounter = 0
_initializedEngine = False

def createWorkflowRunner(configFileName):
	global _runnerIdCounter
	runner = TestRunnerA(configFileName, _runnerIdCounter)
	_runnerIdCounter += 1
	return runner
synchronized('createWorkflowRunner')
# END of Abstract Factory Interface #################################################################################


# Support the Abstract Factory Product ##############################################################################
class ConfManager:
	def __init__(self, configFileName, director):
		self.__director = director
		self.__configFilePath = os.path.join(configManager.getManager().getConfigFolder(), configFileName)
		try:
			with open(self.__configFilePath) as cf:
				self.__config = json.load(cf)
		except Exception as e:
			msg = "Config file " + self.__configFilePath + " could not be read, because " + str(e)
			self.__director.getReporter().error(msg)
			raise WorkflowRunnerException(msg)

	def getWorkflowId(self):
		if "workflowId" not in self.__config:
			msg = "Missing workflow ID from config file " + self.__configFilePath
			self.__director.getReporter().error(msg)
			raise WorkflowRunnerException(msg)
		else:
			return self.__config['workflowId']

	def getConfigFilePath(self):
		return self.__configFilePath

	def getProvides(self):
		if "provides" in self.__config:
			return self.__config['provides']
		else:
			msg = "Missing information about what the workflow provides at config file " + self.__configFilePath
			self.__director.getReporter().error(msg)
			raise WorkflowRunnerException(msg)

	def getRequires(self):
		if "requires" in self.__config:
			return self.__config['requires']
		else:
			msg = "Missing information about what the workflow requires at config file " \
				+ self.__configFilePath
			self.__director.getReporter().error(msg)
			raise WorkflowRunnerException(msg)
# END of Support the Abstract Factory Product #######################################################################


# Abstract Factory Product ##########################################################################################
class TestRunnerA(WorkflowRunner):
	def __init__(self, configFileName, runnerId = 0):
		super(TestRunnerA, self).__init__()
		self.__runnerId = runnerId
		self.__runnerIdName = __name__ + "-" + str(runnerId)
		self.__logger = configManager.getManager().createLogger(self.__runnerIdName)
		self.__reporter = configManager.getManager().createReporter(self.__runnerIdName + "_report")
		self.__logger.debug("Trying to load config file " + configFileName)
		self.__config = ConfManager(configFileName, self)
		self.__logger.debug("Workflow configuration file, " + self.__config.getConfigFilePath())

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
		self.waitForRequirements()
		self.__logger.debug("Executing workflow -- " + self.__config.getWorkflowId() + " --")
		self.__logger.debug("Body of workflow execution")
		self.__logger.debug("End of workflow execution " + self.__config.getWorkflowId())
		self.__reporter.info("Workflow executed successfully! " + self.__config.getWorkflowId())
# END of Abstract Factory Product ###################################################################################

# END OF SCRIPT #####################################################################################################