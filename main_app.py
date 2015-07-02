#!/usr/bin/env python3

#####################################################################################################################
#										Workflow Engine Main Application											#
#####################################################################################################################
#																Author: Manuel Bernal Llinares <mbdebian@gmail.com>	#
#####################################################################################################################

# Import modules from system
import sys
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

	# The code after these lines could be encapsulated in a class that implements the business logic of the Engine,
	# this way, we could have both command line and GUI interfaces.
	error = False
	try:
		if args.testFactory:
			msg = "\nPaths:\n\tWorking dir: " + config.getWorkingDir() \
			+ "\n\tReports folder: " + config.getReportsFolder() \
			+ "\n\tLogs folder: " + config.getLogsFolder() \
			+ "\n\tResources Folder: " + config.getResourcesFolder() \
			+ "\n\tConfig folder: " + config.getConfigFolder()
			config.getReporter().info(msg)
			config.getLogger().debug(msg)
			config.getReporter().info("Test mode for factory: " + args.testFactory)
			config.getLogger().debug("Getting instance of the factory to test")
			wfactory = config.getWorkflowFactoryInstance(args.testFactory)
			msg = "Calling unitTest() method to test factory: " + args.testFactory
			config.getLogger().debug(msg)
			config.getReporter().info(msg)
			wfactory.unitTest()
		else:
			# Instantiate the main Workflow
			try:
				mainWorkflow = config.getMainWorkflowInstance()
				mainWorkflow.execute()
			except Exception as e:
				config.getReporter().error("An exception occurred while running session '" \
					+ config.getSessionId() + "', ERROR message: " + str(e))
				error = True
			else:
				if mainWorkflow.isResultSuccess():
					config.getReporter().info("Successful session: '" + config.getSessionId() + "'")
				else:
					config.getReporter().error("Error running session '" + config.getSessionId() + "', ERROR: " \
						+ mainWorkflow.getResultMessage())
					error = True
			finally:
				if not error:
					# Execute success workflow
					try:
						swf = config.getSuccessWorkflowInstance()
						swf.execute()
					except Exception as e:
						config.getReporter().error("An exception occurred while running the success workflow " \
							+ "for session '" + config.getSessionId() + "', ERROR message: " + str(e))
						error = True
				else:
					# Execute error workflow
					pass
	except Exception as e:
		config.getReporter().error("ERROR!!! " + str(e))
		print(str(e))
		error = True
	finally:
		config.getReporter().info("END of session " + config.getSessionId())
		logging.shutdown()
		if error:
			# TODO Flag the folder as ERROR, so another process knows there was a problem
			sys.exit(1)


if __name__ == "__main__":
	main()