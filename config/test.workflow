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
		}
	},
	"workflow": ["operationB", "operationA"],
	"provides": ["TestWorkflow"],
	"requires": [],
	"provisionKeys": ["opa", "opb"]
}