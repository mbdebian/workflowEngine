#!/usr/bin/env python3

#####################################################################################################################
#												WorkflowRunner Base Class											#
#####################################################################################################################
#																Author: Manuel Bernal Llinares <mbdebian@gmail.com>	#
#####################################################################################################################

# TODO
#	- WorkflowRunner.execute() should be a template method, where subclasses override steps to define final actions
#		that it will take. Designed that way, I could obtain a list of steps to execute, pointing to their 
# 		corresponding runners, and then choose between different strategies to run them (sequencial, distributed, 
#		in parallel...)
# 	- I didn't do it because I'm cutting corners here



# This is the base class for all the Workflows implemented in this tool, it uses the observer pattern because 
# workflows have to be able to subscribe and notify to each other upon termination of their task or subtasks

# Application modules
import os
import json
import threading
import configManager
from exceptions import *
from workflows.observer import *


# Base class for handling configuration
class WfConfManager():
	""" This class handles the Workflow configuration for a WorkflowEngine """
	def __init__(self, configFileName, director):
		self._director = director
		self._configFilePath = os.path.join(configManager.getManager().getConfigFolder(), configFileName)
		try:
			with open(self._configFilePath) as cf:
				self._config = json.load(cf)
		except Exception as e:
			msg = "Config file " + self._configFilePath + " could not be read, because " + str(e)
			self._director.getReporter().error(msg)
			raise WfConfManagerException(msg)

	def _getValueForKey(self, key):
		if key in self._config:
			return self._config[key]
		else:
			msg = "Could not find '" + key + "' in config file " + self._configFilePath
			self._director.getLogger().error(msg)
			raise WfConfManagerException(msg)		

	def getWorkflowId(self):
		key = "workflowId"
		return self._getValueForKey(key)

	def getConfigFilePath(self):
		return self._configFilePath

	def getProvides(self):
		key = "provides"
		return self._getValueForKey(key)

	def getRequires(self):
		key = "requires"
		return self._getValueForKey(key)

# Base class for runners
class WorkflowRunner(Observable, Observer):
	"""docstring for WorkflowRunner"""
	def __init__(self):
		Observer.__init__(self)
		Observable.__init__(self)
		# Default behavior for waiting for observables
		self.__waitingForReqs = set()
		self.__readyToGo = threading.Condition()

	def provides(self):
		raise NotImplementedError("WorkflowRunner - method 'provides' must be implemented by subclasses")

	def requires(self):
		raise NotImplementedError("WorkflowRunner - method 'requires' must be implemented by subclasses")

	def getLogger(self):
		raise NotImplementedError("WorkflowRunner - method 'getLogger' must be implemented by subclasses")

	def getReporter(self):
		raise NotImplementedError("WorkflowRunner - method 'getReporter' must be implemented by subclasses")

	def getId(self):
		raise NotImplementedError("WorkflowRunner - method 'getId' must be implemented by subclasses")

	def getIdName(self):
		raise NotImplementedError("WorkflowRunner - method 'getIdName' must be implemented by subclasses")

	def observe(self, runner, requiredItem):
		""" Implements the default behavior for observing observables """
		self.getLogger().debug("Running default implementation of method 'observe', subscribing runner " \
			+ self.getIdName() + " to runner " + runner.getIdName() + " on requirement " + requiredItem \
			+ " provided by the latter")
		self.__readyToGo.acquire()
		self.__waitingForReqs.add(requiredItem)
		self.__readyToGo.release()
		runner.addObserver(self)
		#raise NotImplementedError("When inheriting from WorkflowRunner you must implement method 'observe'")

	def update(self, runner, arg=None):
		""" Implements default behavior for runners subscribed to other runners """
		self.getLogger().debug("Running default implementation of method 'update', received notification from " \
			+ "runner " + runner.getIdName() + ", provider of " + str(runner.provides()))
		self.__readyToGo.acquire()
		if arg:
			self.getLogger.debug("Runner " + runner.getIdName() + " just provided " + arg)
			self.__waitingForReqs.remove(arg)
		else:
			self.getLogger().debug("Runner " + runner.getIdName() + " provided all its provision keys")
			for provisionKey in runner.provides():
				if provisionKey in self.__waitingForReqs:
					self.__waitingForReqs.remove(provisionKey)
		# Check if we got all our requirements covered
		if len(self.__waitingForReqs) == 0:
			# Notify waiting threads
			self.getLogger().debug("All requirements have been met, notifying all waiting inner threads")
			self.__readyToGo.notifyAll()
		self.__readyToGo.release()

	def jobDone(self, provisionKey = None):
		""" Default behavior for the runner """
		self.getLogger().debug("Notifying observers that I'M DONE, runner " \
			+ self.getIdName())
		self.setChanged()
		self.notifyObservers(provisionKey)

	def waitForRequirements(self):
		self.getLogger().debug("Running default implementation of waiting for requirements to be met, runner " \
			+ self.getIdName())
		self.__readyToGo.acquire()
		while len(self.__waitingForReqs) > 0:
			self.getLogger().debug("This thread woke up, but there still are requirements to be met in the queue")
			self.__readyToGo.wait()
		self.__readyToGo.release()

	def _execute(self):
		""" This method should be overriden by subclasses to put their main execution workflow """
		self.getLogger("YOU SHOULD OVERRIDE method _execute with your workflow execution")
		
	def execute(self):
		""" A kind of template method for workflow executions """
		self.waitForRequirements()
		self._execute()
		self.jobDone()
