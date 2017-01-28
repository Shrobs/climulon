import boto3
import botocore
import os
import re
from handlers import utils
import taskDefs
import services
from handlers.exceptions import (WrongFieldFormat,
                                 NotADockerImageName)


def deploy_handler(args):
    # Handler for deploy by updating infra templates
    conf = args.conf
    imageArgs = args.images

    # Will contain the keys and values for the images that will overwrite those in
    # the master config file
    deployImages = {}

    if imageArgs is None:
        # "Var=image" regex
        argRe = '^[\S]+=[\S]+$'
        argRePattern = re.compile(argRe)

        # Docker image regex
        imageRe = ('^(?:(?=[^:\/]{4,253})(?!-)[a-zA-Z0-9-]{1,63}(?<!-)(?:\.(?!-)'
                   '[a-zA-Z0-9-]{1,63}(?<!-))*(?::[0-9]{1,5})?/)?((?![._-])'
                   '(?:[a-z0-9._-]*)(?<![._-])(?:/(?![._-])[a-z0-9._-]*(?<![._-]))*)'
                   '(?::(?![.-])[a-zA-Z0-9_.-]{1,128})?$')
        imageRePattern = re.compile(imageRe)



        for imageArg in imageArgs:
            if argRePattern.match(imageArg):
                words = imageArg.split("=")
                if len(words) > 2:
                    raise WrongFieldFormat(imageArg)
                var = words[0]
                image = words[1]
                if imageRePattern.match(image):
                    deployImages[var] = image
                else:
                    raise NotADockerImageName(image)
            else:
                raise WrongFieldFormat(imageArg)

    run_deployment(conf, deployImages)


def run_deployment(conf, deployImages):

    if deployImages:
        # Deploy by using updated templates
        print("Using these arguments for image override : %s" % (deployImages))

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

    if deployImages:
        # Overwriting parameters by those provided in the --images option
        for key, value in configParams.items():
            if key in deployImages:
                configParams[key] = deployImages[key]

    if not ComputeStackFound:
        print("ERROR : No stack with ComputeStack set as True is "
              "currently running, cannot deploy")

    tasksDefsContent = taskDefs.fill_taskDef_templates(
        tasksDefsContent, configParams, configOutput)

    taskDefs.register_taskDef(tasksDefsContent, template["StackRegion"])

    servicesContent = services.fill_service_templates(
        servicesContent, configParams, configOutput)

    services.update_services(servicesContent, template["StackRegion"])

    print("Deployment started")
    print("Run `Climulon status` to check the deployment status")
