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
	parser.add_argument("-t", '--test', metavar='testFactory', dest='testFactory', help='run the unit tests for the given WorkflowRunner \
		Factory', type=str)
	args = parser.parse_args()
	return args

def main():
	# Get the command line arguments
	args = getCmdl()
	# Read the configuration
	testmode = False
	if args.testFactory:
		testmode = True
	config = configManager.createConfigManager(args.configFileName, testmode)
	# Mark the start of the session
	config.getReporter().info("Session " + config.getSessionId() + " Started")
	msg = "\nPaths:\n\tWorking dir: " + config.getWorkingDir() \
	+ "\n\tReports folder: " + config.getReportsFolder() \
	+ "\n\tLogs folder: " + config.getLogsFolder() \
	+ "\n\tResources Folder: " + config.getResourcesFolder() \
	+ "\n\tConfig folder: " + config.getConfigFolder()
	config.getReporter().info(msg)
	config.getLogger().debug(msg)

	# The code after these lines could be encapsulated in a class that implements the business logic of the Engine,
	# this way, we could have both command line and GUI interfaces.
	try:
		if args.testFactory:
			config.getReporter().info("Test mode for factory: " + args.testFactory)
		else:
			# Instantiate the main Workflow
			try:
				mainWorkflow = config.getMainWorkflowInstance()
				mainWorkflow.execute()
			except Exception as e:
				config.getReporter().error("Failed to execute the workflow, " + str(e))
				# Remove this line when production
				print(str(e))
	except Exception as e:
		config.getReporter().error("ERROR!!! " + str(e))
		print(str(e))
	finally:
		config.getReporter().info("END of session " + config.getSessionId())
		logging.shutdown()


if __name__ == "__main__":
	main()