#!/usr/bin/env python3

#####################################################################################################################
#							User defined exceptions for Unit Tests of WorkflowRunner								#
#####################################################################################################################
#																Author: Manuel Bernal Llinares <mbdebian@gmail.com>	#
#####################################################################################################################

class AppException(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class ConfigException(AppException):
	def __init__(self, value):
		super(ConfigException, self).__init__(value)

class WorkflowRunnerException(AppException):
	def __init__(self, value):
		super(WorkflowRunnerException, self).__init__(value)

class WfConfManagerException(AppException):
	def __init__(self, value):
		super(WfConfManagerException, self).__init__(value)
