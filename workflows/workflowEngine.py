#!/usr/bin/env python3

#####################################################################################################################
#												Workflow Engine														#
#####################################################################################################################
#																Author: Manuel Bernal Llinares <mbdebian@gmail.com>	#
#####################################################################################################################

# This engine runs workflows defined in a configuration file

# TODO
# - Log exception messages so they can be seen in the reports, finalizing the application in an ordered way
# - Make the factory thread safe




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
	print("WorkflowEngine - Preparing Unit Testing code...")
	# Set up things that we would normally get from the Application wide ConfigManager
	unitTest()
else:
	# We are running as part of the application
	import configManager
	from exceptions import WorkflowRunnerException
	from workflows.workflowRunner import WorkflowRunner
	from workflows.workflowRunner import WfConfManager
	from workflows.Synchronization import *
	_init()
# END of Entry point ################################################################################################




# Modules from the system ###########################################################################################
import os
import json
import threading
# END of Modules from the system ####################################################################################


# Abstract Factory Interface ########################################################################################
_runnerIdCounter = 0
# TODO Remove the following module attribute
_initializedEngine = False

def createWorkflowRunner(configFileName):
	""" It creates an instance of the Workflow runner implemented in this module, and it returns it back to the
	calling client
	"""
	global _runnerIdCounter
	runner = WorkflowEngine(configFileName, _runnerIdCounter)
	_runnerIdCounter += 1
	return runner
# Make the factory thread safe
synchronized('createWorkflowRunner')
# END of Abstract Factory Interface #################################################################################

# Support the Abstract Factory Product ##############################################################################
class WfeConfManager(WfConfManager):
	""" This class handles the Workflow configuration for a WorkflowEngine """
	def __init__(self, configFileName, director):
		WfConfManager.__init__(self, configFileName, director)

	def getOperations(self):
		if "operations" in self._config:
			return list(self._config["operations"].keys())
		else:
			msg = "Missing operations at config file " + self._configFilePath
			self._director.getReporter().error(msg)
			raise WorkflowRunnerException(msg)

	def getFactoryNameForOperation(self, operation):
		if "factory" in self._config["operations"][operation]:
			return self._config["operations"][operation]["factory"]
		else:
			msg = "Missing Factory for operation " + operation + " at config file " \
				+ self._configFilePath
			self._director.getReporter().error(msg)
			raise WorkflowRunnerException(msg)

	def getConfigFileForOperation(self, operation):
		if "configFileName" in self._config["operations"][operation]:
			return self._config["operations"][operation]["configFileName"]
		else:
			msg = "Missing Config File Name for operation " + operation + " at config file "\
				+ self._configFilePath
			self._director.getReporter().error(msg)
			raise WorkflowRunnerException(msg)

	def getWorkflowSequence(self):
		if "workflow" in self._config:
			return self._config["workflow"]
		else:
			msg = "Missing workflow sequence in config file " + self._configFilePath
			self._director.getReporter().error(msg)
			raise WorkflowRunnerException(msg)
# END of Support the Abstract Factory Product #######################################################################


# Abstract Factory Product ##########################################################################################
class WorkflowEngine(WorkflowRunner):
	""" This is a specialization of WorkflowRunner that executes other workflows.
	It is the composite in the composite pattern.
	"""
	def __init__(self, configFileName, runnerId = 0):
		super(WorkflowEngine, self).__init__()
		self.__runnerId = runnerId
		self.__runnerIdName = __name__ + "-" + str(runnerId)
		self.__logger = configManager.getManager().createLogger(self.__runnerIdName)
		self.__reporter = configManager.getManager().createReporter(self.__runnerIdName + "_report")
		self.__logger.debug("Trying to load config file " + configFileName)
		self.__config = WfeConfManager(configFileName, self)
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
		self.__logger.debug("Executing workflow -- " + self.__config.getWorkflowId() + " --")
		# Load runners for the operations
		operations = {}
		for op in self.__config.getOperations():
			try:
				self.__logger.debug("Processing Factory for operation '" + op + "'")
				operations[op] = {}
				operations[op]['factory'] = \
					configManager.getManager().getWorkflowFactoryInstance(self.__config.getFactoryNameForOperation(op))
				self.__logger("Instantiating runner with config file " + self.__config.getConfigFileForOperation(op))
				operations[op]['runner'] = operations[op]['factory'].createWorkflowRunner(self.__config.getConfigFileForOperation(op))
			except Exception as e:
				msg = "An error occurred while trying to instantiate factories and runners for workflow " \
					+ self.__config.getWorkflowId() + "\nERROR: " + str(e)
				self.__reporter.error(msg)
				raise WorkflowRunnerException(msg)
		# Load workflow operation sequence
		wfSequence = self.__config.getWorkflowSequence()
		self.__logger.debug("WORKFLOW SEQUENCE loaded: " + str(wfSequence))
		# Static composition check
		# Subscribe every operation to its providers
		provisions = {}
		for op in wfSequence:
			self.__logger.debug("Processing workflow sequence operation '" + op + "'")
			if len(operations[op]['runner'].requires()) > 0:
				self.__logger.debug("Operation '" + op + "' requires: " + str(operations[op]['runner'].requires()))
				# Sign the runner up for those previous operations in the workflow providing what it needs
				for requiredItem in operations[op]['runner'].requires():
					if requiredItem in provisions:
						# Even if we are using a list for providers of a particular item, I always use the first one
						# on the list, this can be changed later in the future to be more elaborated, but keep in
						# mind that this workflow engine was designed upon the assumption of one single provider
						# per required item
						self.__logger.debug("Making runner " + operations[op]['runner'].getIdName() \
							+ " observe for requirement '" + requiredItem + "' on provider '" \
							+ provisions[requiredItem][0].getIdName() + "'")						
						operations[op]['runner'].observe(provisions[requiredItem][0], requiredItem)
					else:
						msg = "Workflow Processing ERROR - operation " + op + " run by '" \
							+ operations[op]['runner'].getIdName() + "' requires '" + requiredItem \
							+ "' but it is not provided by any of the antecesors of the workflow"
						self.__reporter.error(msg)
						raise WorkflowRunnerException(msg)
			self.__logger.debug("Runner " + operations[op]['runner'].getIdName() + " provides: " \
				+ str(operations[op]['runner'].provides()))
			for provisionKey in operations[op]['runner'].provides():
				self.__logger.debug("Registering that operation '" + op + "' provides " + provisionKey)
				if provisionKey not in provisions:
					# I should not need a list but something tells me that it's better this way
					provisions[provisionKey] = []
				# Add the reference of the runner
				provisions[provisionKey].append(operations[op]['runner'])
		# Run workflows in parallel
		runners = []
		for op in wfSequence:
			self.__logger.debug("Launching thread for operation '" + op + "' being run by runner " \
				+ operations[op]['runner'].getIdName())
			thread = threading.Thread(target=operations[op]['runner'].execute)
			thread.start()
			runners.append(thread)
		self.__logger.debug("Waiting for operations to finish")
		for runner in runners:
			runner.join()
		self.__logger.debug("All runners have finished")
		self.__reporter.info("End of workflow execution " + self.__config.getWorkflowId())
# END of Abstract Factory Product ###################################################################################

# END OF SCRIPT #####################################################################################################