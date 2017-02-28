import boto3
import json
import dependency_engine as engine
from taskDefs.exceptions import TaskDefUnresolvedDependency


def fill_taskDef_templates(tasksDefsContent, configParams):
    # Filling task definition templates with variables
    print("Filling task definition templates with parameters...")
    for taskDef in tasksDefsContent:
        print("Updating task def : %s" % (taskDef))
        missingRefs = engine.dependencyResolver(
            tasksDefsContent[taskDef], resolve=True,
            valueSources=[configParams])
        if missingRefs:
            raise TaskDefUnresolvedDependency(taskDef, missingRefs)
        tasksDefsContent[taskDef] = json.dumps(tasksDefsContent[taskDef])
        print("Task def updated : %s" % (taskDef))
    return tasksDefsContent


def register_taskDef(tasksDefsContent, region):
    # Registering Task definitions
    client = boto3.client('ecs', region_name=region)
    print("Registering Task definitions...")
    for taskDef in tasksDefsContent:
        print("Registering task def : %s" % (taskDef))
        template = json.loads(tasksDefsContent[taskDef])
        taskDefCreateResponse = client.register_task_definition(
            family=template["family"],
            taskRoleArn=template["taskRoleArn"],
            containerDefinitions=template["containerDefinitions"],
            volumes=template["volumes"])
        print("Task def registered : %s" %
              (taskDefCreateResponse["taskDefinition"]
               ["taskDefinitionArn"]))
