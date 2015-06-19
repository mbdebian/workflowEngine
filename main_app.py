#!/usr/bin/env python3

#####################################################################################################################
#										Workflow Engine Main Application											#
#####################################################################################################################
#																Author: Manuel Bernal Llinares <mbdebian@gmail.com>	#
#####################################################################################################################

# Import modules from system
import logging
import argparse
# Import modules from package
import configManager
import exceptions
import workflows.workflowEngine as wfEngineFactory

def getCmdl():
	cmdl_version = '2015.06.15'
	parser = argparse.ArgumentParser(conflict_handler='resolve')
	parser.add_argument("configFileName", metavar='config_file', \
		help='Application configuration file')
	parser.add_argument('-v', '--version', help='display version information', \
		action='version', version=cmdl_version + ' %(prog)s ')
	args = parser.parse_args()
	return args

def main():
	# Get the command line arguments
	args = getCmdl()
	# Read the configuration
	config = configManager.createConfigManager(args.configFileName)
	# Mark the start of the session
	config.getReporter().info("Session " + config.getSessionId() + " Started")
	# The code after these lines could be encapsulated in a class that implements the business logic of the Engine,
	# this way, we could have both command line and GUI interfaces.
	# Instantiate the main Workflow
	try:
		mainWorkflow = config.getMainWorkflowInstance()
		mainWorkflow.execute()
	except Exception as e:
		config.getReporter().error("Failed to execute the workflow, " + str(e))
		# Remove this line when production
		print(str(e))
	finally:
		config.getReporter().info("END of session " + config.getSessionId())
		logging.shutdown()


if __name__ == "__main__":
	main()