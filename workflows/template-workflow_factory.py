#!/usr/bin/env python3

#####################################################################################################################
#											TEMPLATE Workflow Runner												#
#####################################################################################################################
#																Author: Manuel Bernal Llinares <mbdebian@gmail.com>	#
#####################################################################################################################

# This is just a template for creating factories of WorkflowRunner
# It is quite useful to not start from scratch implementing the factories of your concrete workflow runners
# Maybe, I should have done this not only a template, but something like a Supermodule from which other modules
# (workflow runner factories) could inherit (delegate in the case of modules), this way I could always keep the base
# requirements of what you need to implement your own workflow runners, up to date by just updating this template
# Although another way of using this template is by importing it into the namespace, and then subclassing the classes
# defined on it, and redefining the methods of the module. Or importing the module via a reference and both subclass 
# and delegate


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
	print("Preparing Unit Testing code...")
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
import json					# This template already has code to read a config file in JSON format
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
class WfConfManager():
	""" This class handles the Workflow configuration for a WorkflowEngine """
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
class MyWorkflowRunner(WorkflowRunner):
	""" This is a template for the user to create its own workflows
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
		""" This method is where your workflow does its job """
		pass
# END of Abstract Factory Product ###################################################################################

# END OF SCRIPT #####################################################################################################