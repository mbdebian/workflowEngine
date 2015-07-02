{
	"workflowId": "TestWorkflow",
	"operations": {
		"operationB": {
			"factory": "workflowEngine",
			"configFileName": "test_sub.workflow"
		},
		"operationA": {
			"factory": "testRunnerA",
			"configFileName": "testRunnerA_testworkflow.conf"
		},
		"operationError": {
			"factory": "errorRunner",
			"configFileName": "errorRunner.conf"
		}
	},
	"workflow": ["operationB", "operationError", "operationA"],
	"provides": ["TestWorkflow"],
	"requires": [],
	"provisionKeys": ["opa", "opb"]
}