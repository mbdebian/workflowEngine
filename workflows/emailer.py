#!/usr/bin/env python3

#####################################################################################################################
#												Emailer Toolbox 													#
#####################################################################################################################
#																Author: Manuel Bernal Llinares <mbdebian@gmail.com>	#
#####################################################################################################################

""" This module offers an abstraction for sending e-mails from the workflow engine
"""

import os
import time
import subprocess
# Modules from the Workflow Engine
if not __name__ == '__main__':
	import workflows.configManagementToolbox as cmtBox
	import configManager

class EmailerException(Exception):
	def __init__(self, value):
		super(EmailerException, self).__init__()
		self.value = value
	def __str__(self):
		return repr(self.value)

class ConfManager(cmtBox.ConfManager):
	def __init__(self, configFileName, director):
		super(ConfManager, self).__init__(configFileName, director)

	def getUsername(self):
		key = 'sshUser'
		return self._getValueForKey(key)

	def getSshServer(self):
		key = 'sshServer'
		return self._getValueForKey(key)

	def getSendingAttempts(self):
		key = 'sendingAttempts'
		return int(self._getValueForKey(key))

	def getSendingTimeout(self):
		key = 'sendingTimeout'
		return int(self._getValueForKey(key))


class Emailer:
	def __init__(self, configFilePath, client):
		self.__logger = client.getLogger()
		self.__config = ConfManager(configFilePath, self)

	def _sendEmail(self, receiver, subject, contentFilePath, cc=[], cco=[]):
		""" Simple method that uses a SSH reachable server for sending the e-mail, CC and CCO are not supported """
		self.__logger.debug("Sending e-mail to '" + receiver \
			+ "'\n\tSubject: " + subject \
			+ "'\n\tContent: " + contentFilePath
			+ "'\n\tSending Server: " + self.__config.getSshServer()
			+ "'\n\tUsername: " + self.__config.getUsername() \
			+ "'\n\tSending options: " + str(self.__config.getSendingAttempts()) + " attempts, " \
				+ str(self.__config.getSendingTimeout()) + " seconds for operation timeout")
		command = "ssh " + self.__config.getUsername() + "@" + self.__config.getSshServer() \
			+ " \"mail -s '" + subject.replace("\"", " - ") + "' " + receiver + "\""
		stdout = b' '
		stderr = b' '
		nTries = self.__config.getSendingAttempts()
		self.__logger.debug("Sending e-mail using command: " + command)
		while nTries > 0:
			try:
				with open(contentFilePath, "r") as bodyf:
					p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, \
						stdin=bodyf, shell=True)
					(stdout, stderr) = p.communicate(timeout=self.__config.getSendingTimeout())
			except subprocess.TimeoutExpired as t:
				self.__logger.warning("Timeout expired while trying to send e-mail with subject '" + subject + "'" \
					+ "\nERROR: " + str(t))
			except Exception as e:
				msg = "An error occurred while trying to send e-mail with subject '" + subject + "'" \
					+ "\nERROR: " + str(e)
				self.__logger.error(msg)
				raise EmailerException(msg)
			else:
				if p.returncode:
					msg = "Error while trying to send e-mail with subject '" + subject + "'\nERROR: " \
						+ stdout.decode('utf8') + "\n" + stderr.decode('utf8')
					self.__logger.error(msg)
					raise EmailerException(msg)
				else:
					msg = "Command execution for sending e-mail completed, subject '" + subject + "'"
					self.__logger.debug(msg)
					break
			finally:
				nTries -= 1

	def sendEmail(self, receiver, subject, content = 'NO CONTENT HAS BEEN SPECIFIED'):
		tmpFilePath = os.path.join(configManager.getManager().getWorkingDir(), 'emailbody.tmp' + str(int(time.time())))
		with open(tmpFilePath, "w") as tmpf:
			tmpf.write(content)
		try:
			self._sendEmail(receiver, subject, tmpFilePath)
		finally:
			self.__logger.debug("Cleaning temporary file '" + tmpFilePath + "'")
			try:
				os.remove(tmpFilePath)
			except Exception as e:
				self.__logger.warning("ERROR cleaning temporary file '" + tmpFilePath + "'")

	def sendEmailContentFromFile(self, receiver, subject, contentFilePath):
		self._sendEmail(receiver, subject, contentFilePath)

# UNIT TEST - #######################################################################################################
def unitTest(logger):
	logger.info("--- " * 4 + "Executing unit tests for " + os.path.basename(__file__) + " ---" * 4)
	configFile = "emailer-unit_test.conf.sample"
	class Client():
		def __init__(self, logger):
			self.__logger = logger
		def getLogger(self):
			return self.__logger
	client = Client(logger)
	emailer = Emailer(configFile, client)
	emailer.sendEmail("mbdebian@gmail.com", "Mensaje de prueba desde el emailer", "Contenido de prueba")

# Prevent execution of this module in stand alone mode ##############################################################
if __name__ == "__main__":
	import sys
	sys.stderr.writelines("This module is not designed to be run alone, please, test it using the Workflow Engine")
#####################################################################################################################
