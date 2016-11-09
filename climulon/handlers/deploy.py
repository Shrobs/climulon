import boto3
import botocore
import os
import re
from handlers import utils
import taskDefs
import services


def deploy_handler(args):
    # Handler for deploy by updating infra templates
    conf = args.conf

    # Check if "CI_BRANCH" is in the X.X.X format, if so use it as tag
    # Else use "CI_BRANCH--CI_COMMIT_ID" as tag
    tag = os.environ['CI_BRANCH']
    pattern = re.compile("^\d+\.\d+\.\d+$")
    if not pattern.match(tag):
        tag = os.environ['CI_BRANCH'] + "--" + os.environ['CI_COMMIT_ID']

    run_deployment(conf, tag)


def run_deployment(conf, tag):
    # Deploy by using updated templates
    print("Using tag : %s" % (tag))
    ComputeStackFound = False

    (config, configParams, templates, tasksDefsContent,
     servicesContent) = utils.check_and_get_conf(conf)

    utils.change_workdir(conf)

    for template in templates:
        configOutput = {}
        client = boto3.client('cloudformation', region_name=template["StackRegion"])
        try:
            describeStackResponse = client.describe_stacks(
                StackName=template["StackName"])
            stack = describeStackResponse["Stacks"][0]
            stackOutputs = stack["Outputs"]

            print("Getting stack output from %s" % (template["StackName"]))
            for outputSet in stackOutputs:
                configOutput[outputSet["OutputKey"]
                             ] = outputSet["OutputValue"]

            utils.mergeOutputConfig(configOutput, configParams, template)

            if template["ComputeStack"].lower() == "true":
                ComputeStackFound = True
        except botocore.exceptions.ClientError as e:
            if (e.response['Error']['Code'] ==
                    'ValidationError' and
                    "does not exist" in
                    e.response['Error']['Message']):
                print("Stack %s not found, ignoring" %
                      (template["StackName"]))
            else:
                raise

    # Updating built images tags (images that are marked by BUILD_IMAGE_*)
    for key, value in configParams.items():
        if "BUILD_IMAGE" in key:
            buildImageTag = value.split(":", 1)[0] + ":" + tag
            configParams[key] = buildImageTag

    if not ComputeStackFound:
        print("ERROR : No stack with ComputeStack set as True is "
              "currently running, cannot deploy")

    tasksDefsContent = taskDefs.fill_taskDef_templates(
        tasksDefsContent, configParams, configOutput)

    taskDefs.register_taskDef(tasksDefsContent, template["StackRegion"])

    servicesContent = services.fill_service_templates(
        servicesContent, configParams, configOutput)

    services.update_services(servicesContent, template["StackRegion"])

    print("Deployment complete")
