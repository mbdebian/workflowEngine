{
	"workflowId": "test_subworkflow",
	"operations": {
		"operationB": {
			"factory": "testRunnerA",
			"configFileName": "testRunnerA_subopA.conf"
		},
		"operationA": {
			"factory": "testRunnerA",
			"configFileName": "testRunnerA_subopB.conf"
		}
	},
	"workflow": ["operationA", "operationB"],
	"provides": ["opb"],
	"requires": [],
	"provisionKeys": []
}