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

# Application defaults - NORMAL OPERATION MODE
_configFolder = os.path.abspath('config')
_workflowsModulePrefix = 'workflows'
_workflowsFolder = os.path.abspath(_workflowsModulePrefix)
_runFolder = os.path.abspath('run')
_resourcesFolder = os.path.abspath('resources')
_ipcFolder = os.path.abspath('ipc')
# Extra defaults - UNIT TESTING OPERATION MODE
_testFolder = os.path.abspath("test")
_sessionWorkingDir = '/tmp'

# Common defaults
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

def createConfigManager(configFileName, testmode=False):
	global _configManager
	global _configFolder
	#global _workflowsFolder
	global _runFolder
	global _resourcesFolder
	global _ipcFolder
	global _sessionWorkingDir
	if _configManager == None:
		if testmode:
			_configFolder = os.path.join(_testFolder, "config")
			#_workflowsFolder = os.path.join(_testFolder, "workflows")
			_runFolder = os.path.join(_testFolder, "run")
			_sessionWorkingDir = _runFolder
			_resourcesFolder = os.path.join(_testFolder, "resources")
			_ipcFolder = os.path.join(_testFolder, "ipc")
		# Read the file
		try:
			configFilePath = os.path.abspath(os.path.join(_configFolder, configFileName))
			with open(configFilePath) as cf:
				# Load JSON formatted config
				configObject = json.load(cf)
		except Exception as e:
			raise ConfigException(str(e))
		# Instantiate the ConfigManager
		if testmode:
			_configManager = TestConfigManager(configObject)
		else:
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
			self.__runFolder = _runFolder
		else:
			self.__runFolder = configObject['runFolder']
		# Make the PATH absolute
		self.__runFolder = os.path.abspath(self.__runFolder)
		dirsToCheck.append(self.__runFolder)
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
			self.__sessionId = time.strftime('%Y.%m.%d_%H.%M') + "-" + configObject['jobId']
		except Exception as e:
			raise ConfigException("Error while trying to set up session ID, " + str(e))
		# Create session working dir
		self.__sessionWorkingDir = os.path.abspath(os.path.join(self.__runFolder, self.__sessionId))
		try:
			os.mkdir(self.__sessionWorkingDir)
		except Exception as e:
			raise ConfigException("ERROR while trying to create a working dir for session " \
				+ self.__sessionId + ", " + str(e))
		# Create session log folder
		self.__sessionLogFolder = os.path.abspath(os.path.join(self.__sessionWorkingDir, 'logs'))
		try:
			os.mkdir(self.__sessionLogFolder)
		except Exception as e:
			raise ConfigException("Could not create log folder " + self.__sessionLogFolder + ", error " + str(e))
		# Load logger configuration
		self.__logLevel = _logLevel
		if "loglevel" in configObject['logger']:
			self.__logLevel = configObject['logger']['loglevel']
		configuredLogFormatters = _loggerFormatters
		if "formatters" in configObject['logger']['loglevel']:
			configuredLogFormatters = configObject['logger']['loglevel']['formatters']
		self.__logHandlers = []
		logHandlersPrefix = configObject['jobId'] + '-'
		logHandlersExtension = '.log'
		# Get own logger
		self.__logger = logging.getLogger(__name__)
		self.__logger.setLevel(getattr(logging, self.__logLevel))
		for llevel, lformat in configuredLogFormatters.items():
			logfile = os.path.join(self.__sessionLogFolder, logHandlersPrefix + llevel.lower() + logHandlersExtension)
			lformatter = logging.Formatter(lformat)
			lhandler = logging.FileHandler(logfile, mode='w')
			lhandler.setLevel(getattr(logging, llevel))
			lhandler.setFormatter(lformatter)
			self.__logHandlers.append(lhandler)
			# Add the handlers to my own logger
			self.__logger.addHandler(lhandler)
		self.__logger.debug("Logging system initialized")
		# Initialize reports
		self.__sessionReportsFolder = os.path.abspath(os.path.join(self.__sessionWorkingDir, 'reports'))
		try:
			os.mkdir(self.__sessionReportsFolder)
		except Exception as e:
			raise ConfigException("Could not create reports folder " + self.__sessionReportsFolder + ", error " + str(e))
		# TODO Check config file for formatting options
		self.__reportFormatters = _reportFormatters
		reportFileNormal = os.path.join(self.__sessionReportsFolder, configObject['jobId'] + '.report')
		reportFileWarnings = os.path.join(self.__sessionReportsFolder, configObject['jobId'] + '-warn_err.report')
		normalHandler = logging.FileHandler(reportFileNormal, mode="w")
		warnerrHandler = logging.FileHandler(reportFileWarnings, mode="w")
		normalHandler.setLevel(logging.INFO)
		warnerrHandler.setLevel(logging.WARN)
		normalHandler.setFormatter(logging.Formatter(self.__reportFormatters['normal']))
		warnerrHandler.setFormatter(logging.Formatter(self.__reportFormatters['warnerr']))
		self.__reporter = logging.getLogger(configObject['jobId'] + '-main')
		self.__reporter.addHandler(normalHandler)
		self.__reporter.addHandler(warnerrHandler)
		self.__reporter.setLevel(logging.INFO)
		self.__reportHandlers = [normalHandler, warnerrHandler]
		self.__resourcesFolder = os.path.abspath(_resourcesFolder)

	def getReporter(self):
		""" It returns the main reporter created by the ConfigManager """
		return self.__reporter

	def createReporter(self, name):
		""" Return a reporter customized for the given name """
		rep = logging.getLogger(name)
		for handler in self.__reportHandlers:
			rep.addHandler(handler)
		rep.setLevel(logging.INFO)
		return rep

	def getSessionId(self):
		return self.__sessionId

	def getLogHandlers(self):
		""" Return the log handlers so other modules can use the same ones, but requesting different loggers. """
		return self.__logHandlers

	def getLogLevel(self):
		""" Return the log level currently being used."""
		return self.__logLevel

	def createLogger(self, name):
		""" Return a logger customized for the given name """
		self.__logger.debug("Creating logger with name " + name)
		lg = logging.getLogger(name)
		for handler in self.__logHandlers:
			lg.addHandler(handler)
		lg.setLevel(getattr(logging, self.__logLevel))
		return lg

	def getConfigFolder(self):
		return _configFolder

	def getWorkflowFactoryInstance(self, factoryName):
		self.__logger.debug("Getting instance of Factory '" + factoryName + "'")
		moduleName = _workflowsModulePrefix + "." + factoryName
		instance = None
		try:
			instance = importlib.import_module(moduleName)
		except Exception as e:
			msg = "Error instantiating module " + moduleName + "\nERROR: " + str(e)
			self.__reporter.error(msg)
			raise ConfigException(msg)
		else:
			self.__logger.debug("Instance created!")
		self.__logger.debug("Returning instance of factory " + moduleName)
		return instance

	def getMainWorkflowInstance(self):
		if "mainWorkflow" in self.__configObject:
			# Get Factory instance
			wfFactory = self.getWorkflowFactoryInstance(self.__configObject['mainWorkflow']['factory'])
			if "config" in self.__configObject['mainWorkflow']:
				return wfFactory.createWorkflowRunner(self.__configObject['mainWorkflow']['config'])
			else:
				msg = "There is no config file for the main workflow"
				self.__reporter.error(msg)
				raise ConfigException(msg)

	def getWorkingDir(self):
		return self.__sessionWorkingDir

	def getReportsFolder(self):
		return self.__sessionReportsFolder

	def getLogsFolder(self):
		return self.__sessionLogFolder

	def getResourcesFolder(self):
		return self.__resourcesFolder


# UNIT TEST - Config Manager for unit testing factories #############################################################
class TestConfigManager:
	def __init__(self, configObject):
		self.__configObject = configObject
		dirsToCheck = []
		if "runFolder" not in configObject:
			self.__runFolder = _runFolder
		else:
			self.__runFolder = configObject['runFolder']
		# Make the PATH absolute
		self.__runFolder = os.path.abspath(self.__runFolder)
		self.__sessionWorkingDir = _sessionWorkingDir
		self.__sessionLogFolder = os.path.abspath(os.path.join(self.__sessionWorkingDir, 'logs'))
		self.__sessionReportsFolder = os.path.abspath(os.path.join(self.__sessionWorkingDir, 'reports'))
		dirsToCheck.append(self.__runFolder)
		dirsToCheck.append(self.__sessionWorkingDir)
		dirsToCheck.append(self.__sessionLogFolder)
		dirsToCheck.append(self.__sessionReportsFolder)
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
			self.__sessionId = time.strftime('%Y.%m.%d_%H.%M') + "-" + configObject['jobId']
		except Exception as e:
			raise ConfigException("Error while trying to set up session ID, " + str(e))
		# Load logger configuration
		self.__logLevel = _logLevel
		if "loglevel" in configObject['logger']:
			self.__logLevel = configObject['logger']['loglevel']
		configuredLogFormatters = _loggerFormatters
		if "formatters" in configObject['logger']['loglevel']:
			configuredLogFormatters = configObject['logger']['loglevel']['formatters']
		self.__logHandlers = []
		logHandlersPrefix = configObject['jobId'] + '-'
		logHandlersExtension = '.log'
		# Get own logger
		self.__logger = logging.getLogger(__name__)
		self.__logger.setLevel(getattr(logging, self.__logLevel))
		for llevel, lformat in configuredLogFormatters.items():
			logfile = os.path.join(self.__sessionLogFolder, logHandlersPrefix + llevel.lower() + logHandlersExtension)
			lformatter = logging.Formatter(lformat)
			lhandler = logging.FileHandler(logfile, mode='w')
			lhandler.setLevel(getattr(logging, llevel))
			lhandler.setFormatter(lformatter)
			self.__logHandlers.append(lhandler)
			# Add the handlers to my own logger
			self.__logger.addHandler(lhandler)
		consoleHandler = logging.StreamHandler()
		consoleHandler.setLevel(logging.DEBUG)
		consoleHandler.setFormatter(logging.Formatter(_loggerFormatters['DEBUG']))
		self.__logger.addHandler(consoleHandler)
		self.__logger.debug("Logging system initialized")
		# TODO Check config file for formatting options
		self.__reportFormatters = _reportFormatters
		reportFileNormal = os.path.join(self.__sessionReportsFolder, configObject['jobId'] + '.report')
		reportFileWarnings = os.path.join(self.__sessionReportsFolder, configObject['jobId'] + '-warn_err.report')
		normalHandler = logging.FileHandler(reportFileNormal, mode="w")
		warnerrHandler = logging.FileHandler(reportFileWarnings, mode="w")
		normalHandler.setLevel(logging.INFO)
		warnerrHandler.setLevel(logging.WARN)
		normalHandler.setFormatter(logging.Formatter(self.__reportFormatters['normal']))
		warnerrHandler.setFormatter(logging.Formatter(self.__reportFormatters['warnerr']))
		self.__reporter = logging.getLogger(configObject['jobId'] + '-main')
		self.__reporter.addHandler(normalHandler)
		self.__reporter.addHandler(warnerrHandler)
		self.__reporter.setLevel(logging.INFO)
		self.__reportHandlers = [normalHandler, warnerrHandler]
		self.__resourcesFolder = os.path.abspath(_resourcesFolder)

	def getReporter(self):
		""" It returns the main reporter created by the ConfigManager """
		return self.__reporter

	def createReporter(self, name):
		""" Return a reporter customized for the given name """
		rep = logging.getLogger(name)
		for handler in self.__reportHandlers:
			rep.addHandler(handler)
		rep.setLevel(logging.INFO)
		return rep

	def getSessionId(self):
		return self.__sessionId

	def getLogHandlers(self):
		""" Return the log handlers so other modules can use the same ones, but requesting different loggers. """
		return self.__logHandlers

	def getLogLevel(self):
		""" Return the log level currently being used."""
		return self.__logLevel

	def createLogger(self, name):
		""" Return a logger customized for the given name """
		self.__logger.debug("Creating logger with name " + name)
		lg = logging.getLogger(name)
		for handler in self.__logHandlers:
			lg.addHandler(handler)
		lg.setLevel(getattr(logging, self.__logLevel))
		return lg

	def getConfigFolder(self):
		return _configFolder

	def getWorkflowFactoryInstance(self, factoryName):
		self.__logger.debug("Getting instance of Factory '" + factoryName + "'")
		moduleName = _workflowsModulePrefix + "." + factoryName
		self.__logger.debug("Instantiating module: " + moduleName)
		instance = None
		try:
			instance = importlib.import_module(moduleName)
		except Exception as e:
			msg = "Error instantiating module " + moduleName + "\nERROR: " + str(e)
			self.__reporter.error(msg)
			raise ConfigException(msg)
		else:
			self.__logger.debug("Instance created!")
		self.__logger.debug("Returning instance of factory " + moduleName)
		return instance

	def getWorkingDir(self):
		return self.__sessionWorkingDir

	def getReportsFolder(self):
		return self.__sessionReportsFolder

	def getLogsFolder(self):
		return self.__sessionLogFolder

	def getResourcesFolder(self):
		return self.__resourcesFolder

	def getLogger(self):
		return self.__logger

# END of UNIT TEST - Config Manager for unit testing factories ######################################################
