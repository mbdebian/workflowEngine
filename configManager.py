#!/usr/bin/env python3

#####################################################################################################################
#										Application Wide Config Manager												#
#####################################################################################################################
#																Author: Manuel Bernal Llinares <mbdebian@gmail.com>	#
#####################################################################################################################

# This module implements a kind of a singleton for the application configuration
# to be available application wide

# TODO
# 	- Make use of pseudo-private variables
#	- Implement the part that handles the "resources" and "ipc" folders

# System modules
import os
import time
import json
import logging
import importlib
# Package modules
from exceptions import ConfigException

# Application defaults
_configFolder = 'config'
_workflowsFolder = 'workflows'
_runFolder = 'run'
_loggerFormatters = {
	'DEBUG': '%(asctime)s [%(levelname)s][%(name)s] [%(module)s, %(lineno)s] %(message)s',
	'INFO': '%(asctime)s [%(levelname)s][%(name)s] %(message)s'
}
_logLevel = 'DEBUG'
_reportFormatters = {
	'normal': '%(asctime)s [%(module)s][%(name)s] %(message)s',
	'warnerr': '%(asctime)s [%(levelname)s][%(module)s][%(name)s] %(message)s'
}

# Singleton
_configManager = None

def createConfigManager(configFileName):
	global _configManager
	if _configManager == None:
		# Read the file
		try:
			configFilePath = os.path.join(_configFolder, configFileName)
			with open(configFilePath) as cf:
				# Load JSON formatted config
				configObject = json.load(cf)
		except Exception as e:
			raise ConfigException(str(e))
		# Instantiate the ConfigManager
		_configManager = ConfigurationManager(configObject)
	return _configManager

def getManager():
	global _configManager
	if _configManager:
		return _configManager
	else:
		raise ConfigException("ConfigManager has not been initialized yet!")


class ConfigurationManager:
	def __init__(self, configObject):
		self.__configObject = configObject
		dirsToCheck = []
		if "runFolder" not in configObject:
			self.runFolder = _runFolder
		else:
			self.runFolder = configObject['runFolder']
		dirsToCheck.append(self.runFolder)
		# Check dirs
		for folder in dirsToCheck:
			if not os.path.isdir(folder):
				if os.path.exists(folder):
					raise ConfigException(folder + " is not a folder")
				else:
					try:
						os.mkdir(folder)
					except Exception as e:
						raise ConfigException(str(e))
		# If we get here, we can keep going
		try:
			self.sessionId = time.strftime('%Y.%m.%d_%H.%M') + "-" + configObject['jobId']
		except Exception as e:
			raise ConfigException("Error while trying to set up session ID, " + str(e))
		# Create session working dir
		self.sessionWorkingDir = os.path.join(self.runFolder, self.sessionId)
		try:
			os.mkdir(self.sessionWorkingDir)
		except Exception as e:
			raise ConfigException("ERROR while trying to create a working dir for session " \
				+ self.sessionId + ", " + str(e))
		# Create session log folder
		self.sessionLogFolder = os.path.join(self.sessionWorkingDir, 'logs')
		try:
			os.mkdir(self.sessionLogFolder)
		except Exception as e:
			raise ConfigException("Could not create log folder " + self.sessionLogFolder + ", error " + str(e))
		# Load logger configuration
		self.logLevel = _logLevel
		if "loglevel" in configObject['logger']:
			self.logLevel = configObject['logger']['loglevel']
		configuredLogFormatters = _loggerFormatters
		if "formatters" in configObject['logger']['loglevel']:
			configuredLogFormatters = configObject['logger']['loglevel']['formatters']
		self.logHandlers = []
		logHandlersPrefix = configObject['jobId'] + '-'
		logHandlersExtension = '.log'
		# Get own logger
		self.logger = logging.getLogger(__name__)
		self.logger.setLevel(getattr(logging, self.logLevel))
		for llevel, lformat in configuredLogFormatters.items():
			logfile = os.path.join(self.sessionLogFolder, logHandlersPrefix + llevel.lower() + logHandlersExtension)
			lformatter = logging.Formatter(lformat)
			lhandler = logging.FileHandler(logfile, mode='w')
			lhandler.setLevel(getattr(logging, llevel))
			lhandler.setFormatter(lformatter)
			self.logHandlers.append(lhandler)
			# Add the handlers to my own logger
			self.logger.addHandler(lhandler)
		self.logger.debug("Logging system initialized")
		# Initialize reports
		self.sessionReportsFolder = os.path.join(self.sessionWorkingDir, 'reports')
		try:
			os.mkdir(self.sessionReportsFolder)
		except Exception as e:
			raise ConfigException("Could not create reports folder " + self.sessionReportsFolder + ", error " + str(e))
		# TODO Check config file for formatting options
		self.reportFormatters = _reportFormatters
		reportFileNormal = os.path.join(self.sessionReportsFolder, configObject['jobId'] + '.report')
		reportFileWarnings = os.path.join(self.sessionReportsFolder, configObject['jobId'] + '-warn_err.report')
		normalHandler = logging.FileHandler(reportFileNormal, mode="w")
		warnerrHandler = logging.FileHandler(reportFileWarnings, mode="w")
		normalHandler.setLevel(logging.INFO)
		warnerrHandler.setLevel(logging.WARN)
		normalHandler.setFormatter(logging.Formatter(self.reportFormatters['normal']))
		warnerrHandler.setFormatter(logging.Formatter(self.reportFormatters['warnerr']))
		self.reporter = logging.getLogger(configObject['jobId'] + '-main')
		self.reporter.addHandler(normalHandler)
		self.reporter.addHandler(warnerrHandler)
		self.reporter.setLevel(logging.INFO)
		self.reportHandlers = [normalHandler, warnerrHandler]

	def getReporter(self):
		""" It returns the main reporter created by the ConfigManager """
		return self.reporter

	def createReporter(self, name):
		""" Return a reporter customized for the given name """
		rep = logging.getLogger(name)
		for handler in self.reportHandlers:
			rep.addHandler(handler)
		rep.setLevel(logging.INFO)
		return rep

	def getSessionId(self):
		return self.sessionId

	def getLogHandlers(self):
		""" Return the log handlers so other modules can use the same ones, but requesting different loggers. """
		return self.logHandlers

	def getLogLevel(self):
		""" Return the log level currently being used."""
		return self.logLevel

	def createLogger(self, name):
		""" Return a logger customized for the given name """
		self.logger.debug("Creating logger with name " + name)
		lg = logging.getLogger(name)
		for handler in self.logHandlers:
			lg.addHandler(handler)
		lg.setLevel(getattr(logging, self.logLevel))
		return lg

	def getConfigFolder(self):
		return _configFolder

	def getWorkflowFactoryInstance(self, factoryName):
		self.logger.debug("Getting instance of Factory '" + factoryName + "'")
		moduleName = _workflowsFolder + "." + factoryName
		try:
			return importlib.import_module(moduleName)
		except Exception as e:
			msg = "Error instantiating module " + moduleName
			self.reporter.error(msg + " " + str(e))
			raise ConfigException(msg)

	def getMainWorkflowInstance(self):
		if "mainWorkflow" in self.__configObject:
			# Get Factory instance
			wfFactory = self.getWorkflowFactoryInstance(self.__configObject['mainWorkflow']['factory'])
			if "config" in self.__configObject['mainWorkflow']:
				return wfFactory.createWorkflowRunner(self.__configObject['mainWorkflow']['config'])
			else:
				msg = "There is no config file for the main workflow"
				self.reporter.error(msg)
				raise ConfigException(msg)

