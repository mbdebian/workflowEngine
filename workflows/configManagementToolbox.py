#####################################################################################################################
#											Config Management Toolbox												#
#####################################################################################################################
#																Author: Manuel Bernal Llinares <mbdebian@gmail.com>	#
#####################################################################################################################

""" This module provides tools for managing configuration files and config properties """

import os
import json
import configManager

class ConfManagerException(Exception):
	def __init__(self, value):
		Exception.__init__(self)
		self.value = value
	def __str__(self):
		return repr(self.value)


class ConfManager():
	""" This class handles the Workflow configuration for a WorkflowEngine """
	def __init__(self, configFileName, director):
		self._director = director
		self._configFilePath = configFileName
		if not os.path.isabs(configFileName):
			self._configFilePath = os.path.join(configManager.getManager().getConfigFolder(), configFileName)
		try:
			with open(self._configFilePath) as cf:
				self._config = json.load(cf)
		except Exception as e:
			msg = "Config file " + self._configFilePath + " could not be read, because " + str(e)
			self._director.getLogger().error(msg)
			raise ConfManagerException(msg)

	def _getValueForKey(self, key):
		if key in self._config:
			return self._config[key]
		else:
			msg = "Could not find '" + key + "' in config file " + self._configFilePath
			self._director.getLogger().error(msg)
			raise ConfManagerException(msg)

	def getConfigObject(self):
		return self._config
