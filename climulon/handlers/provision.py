import boto3
import botocore
import time
from handlers import utils
import dependency_engine as engine
import taskDefs
import services
from handlers.exceptions import (StackExistsError,
                                 TaskDefExistsError,
                                 EcsClusterExistsError,
                                 StackUnresolvedDependency,
                                 ExternalStackNotFound)


def provision_handler(args):
    # Handler for both codeship and regular cli, for provision using
    # cloudformation stacks
    conf = args.conf
    stackSubset = args.stacks
    timeout = args.timeout
    if timeout is None:
        timeout = 60
    dry_run = args.dry_run
    run_provision(conf, stackSubset, timeout, dry_run)


def run_provision(conf, stackSubset, timeout, dry_run):
    (config, configParams, templates, tasksDefsContent,
     servicesContent, externalStacks) = utils.check_and_get_conf(conf)

    if stackSubset:
        print("Stack list detected, will only provision this sub-set "
              "of stacks :")
        print(stackSubset)
    else:
        stackSubset = []
        for template in templates:
            stackSubset.append(template["StackName"])

    ComputeStackFound = utils.verify_subset(stackSubset, templates)

    utils.change_workdir(conf)

    # Checking that all the external stacks exist
    if externalStacks:
        print("Checking if external templates exist")
        for stack in externalStacks:
            client = boto3.client('cloudformation', region_name=stack["StackRegion"])
            try:
                response = client.describe_stacks(StackName=stack["StackName"])
            except botocore.exceptions.ClientError as e:
                if (e.response['Error']['Code'] ==
                        'ValidationError' and
                        "does not exist" in
                        e.response['Error']['Message']):
                    raise ExternalStackNotFound(stack["StackName"])
                else:
                    raise
        print("All external stacks available")

    # Checking if there are existant stacks with the names of the templates
    # to be created
    print("Checking if there are CF stack with current names")
    for template in templates:
        if template["StackName"] not in stackSubset:
            continue
    
        client = boto3.client('cloudformation', region_name=template["StackRegion"])

        listStacksResponse = client.list_stacks(
            StackStatusFilter=[
                'CREATE_IN_PROGRESS',
                'CREATE_COMPLETE',
                'ROLLBACK_IN_PROGRESS',
                'ROLLBACK_FAILED',
                'ROLLBACK_COMPLETE',
                'DELETE_IN_PROGRESS',
                'DELETE_FAILED',
                'UPDATE_IN_PROGRESS',
                'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
                'UPDATE_COMPLETE',
                'UPDATE_ROLLBACK_IN_PROGRESS',
                'UPDATE_ROLLBACK_FAILED',
                'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
                'UPDATE_ROLLBACK_COMPLETE'
            ]
        )

        for stack in listStacksResponse["StackSummaries"]:
            if stack["StackName"] == template["StackName"]:
                raise StackExistsError(template["StackName"])

        if template["ComputeStack"].lower() == "true":
            # Checking if there are task defs with same names
            print("Checking if there are task defs with current names")
            client = boto3.client('ecs', region_name=template["StackRegion"])
            for key, value in config["globalParameters"].items():
                if "TASK_DEF_NAME" in key:
                    similarTaskDefs = client.list_task_definition_families(
                        familyPrefix=value, status="ACTIVE")
                    for task in similarTaskDefs['families']:
                        if value == task:
                            raise TaskDefExistsError(task)

            # Checking if there is an ECS cluster with same name
            print("Checking if there is an ECS cluster with current name")
            checkClusterResponse = client.describe_clusters(
                clusters=[configParams["EcsClusterName"]]
            )
            if (checkClusterResponse["clusters"] != [] and
                    checkClusterResponse["clusters"][0]["status"] !=
                    "INACTIVE"):
                raise EcsClusterExistsError(configParams["EcsClusterName"])

    print("Checks complete, ready for provisioning")

    if dry_run is True:
        return

    # Stacks Creation
    print("Creating Stacks...")

    # Will be filled with the output of the created stack at the end of
    # each loop
    configOutput = {}
    for template in templates:
        if template["StackName"] in stackSubset:
            print("Creating stack : %s" % (template["StackName"]))
        else:
            print("Getting output from stack %s if it exists" %
                  (template["StackName"]))

        print("Converting stack config for %s..." %
              (template["StackName"]))

        # Output of the current running stack, will be filled later
        stackOutputs = None
        if template["StackName"] in stackSubset:
            missingRefs = engine.dependencyResolver(
                target=template["StackParameters"],
                resolve=True,
                valueSources=[configParams])
            if missingRefs:
                raise StackUnresolvedDependency(
                    template["StackName"], missingRefs)

            parameterList = []
            for key in template["StackParameters"]:
                param = {
                    'ParameterKey': key,
                    'ParameterValue': template["StackParameters"][key],
                    'UsePreviousValue': False
                }
                parameterList.append(param)

            client = boto3.client('cloudformation', region_name=template["StackRegion"])

            createStackResponse = client.create_stack(
                StackName=template["StackName"],
                TemplateBody=template["TemplateContent"],
                Parameters=parameterList,
                TimeoutInMinutes=timeout,
                Capabilities=[
                    'CAPABILITY_IAM',
                ]
            )
            stackId = createStackResponse["StackId"]
            print("Stack creation launched for stack : %s" %
                  (template["StackName"]))
            print(stackId)

            # Waiting for stack creation
            while True:
                describeStackResponse = client.describe_stacks(
                    StackName=template["StackName"])
                stack = describeStackResponse["Stacks"][0]
                if (stack["StackStatus"] == 'CREATE_FAILED' or
                        stack["StackStatus"] == 'ROLLBACK_COMPLETE'):
                    print("Stack creating failed")
                    print(stack["StackStatusReason"])
                elif stack["StackStatus"] == 'CREATE_COMPLETE':
                    print("Stack creation complete")
                    if "Outputs" in stack:
                        print("Stack Output :")
                        stackOutputs = stack["Outputs"]
                    else:
                        print("Stack with no output to print")
                        stackOutputs = None
                    break
                else:
                    print("Stack creation in progress")
                    time.sleep(20)
        else:
            print("Getting stack output")
            for stack in listStacksResponse["StackSummaries"]:
                if stack["StackName"] == template["StackName"]:
                    print("Stack found")
                    client = boto3.client('cloudformation', region_name=template["StackRegion"])
                    describeStackResponse = client.describe_stacks(
                        StackName=template["StackName"])
                    stack = describeStackResponse["Stacks"][0]
                    if "Outputs" in stack:
                        print("Stack Output :")
                        stackOutputs = stack["Outputs"]
                    else:
                        print("Stack with no output to print")
                        stackOutputs = None
            if not stackOutputs:
                print("Stack does not exist, ignoring step")

        configOutput = {}
        if stackOutputs:
            print("Converting stack output...")
            for outputSet in stackOutputs:
                configOutput[outputSet["OutputKey"]
                             ] = outputSet["OutputValue"]
            print("Output parameters from stack:")
            print(configOutput)

            utils.mergeOutputConfig(configOutput, configParams, template)

        if template["ComputeStack"].lower() == "true" and template["StackName"] in stackSubset:
            tasksDefsContent = taskDefs.fill_taskDef_templates(
                tasksDefsContent, configParams)

            taskDefs.register_taskDef(tasksDefsContent, template["StackRegion"])

            client = boto3.client('ecs', region_name=template["StackRegion"])

            # Create the cluster in ECS
            print("Creating cluster : %s" %
                  (configParams["EcsClusterName"]))
            client.create_cluster(
                clusterName=configParams["EcsClusterName"])
            print("Cluster created : %s" %
                  (configParams["EcsClusterName"]))

            servicesContent = services.fill_service_templates(
                servicesContent, configParams)

            services.create_services(servicesContent, template["StackRegion"])

    print("Provision process successful")
