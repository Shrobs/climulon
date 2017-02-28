import json
import os
import boto3
import dependency_engine.engine as engine
from handlers.exceptions import (RequiredConfigFieldError,
                                 RequiredTemplateFieldError,
                                 FileNotFoundError,
                                 JsonFormatError,
                                 ConfigIntersectionError,
                                 SubsetStackError,
                                 UnsupportedRegionStackError,
                                 RequiredExtStackFieldError)


def checkConfigFile(path):
    requiredFieldsConfig = [
        "infrastructureTemplates",
        "taskDefsTemplates",
        "servicesTemplates",
        "globalParameters"
    ]

    requiredFieldsTemplates = [
        "StackTemplate",
        "StackName",
        "StackOrder",
        "StackParameters",
        "StackRegion",
        "ComputeStack"
    ]

    requiredFieldsExtStacks = [
        "StackName",
        "StackRegion"
    ]

    print("Checking that config file exists and is valid")
    checkFileExists(path)

    # Checking that config file is Json formatted
    checkIsJson(path)

    with open(path, 'r') as configFile:
        config = json.load(configFile)

    # Checking that all required config file fields are available
    for field in requiredFieldsConfig:
        if field not in config:
            raise RequiredConfigFieldError(field)

    # Checking that all required template fields are available
    for stack in config["infrastructureTemplates"]:
        for field in requiredFieldsTemplates:
            if field not in stack:
                raise RequiredTemplateFieldError(field, stack)

    # If external stack key exists, check that it contains the required fields
    externalStacks = []
    if "externalStacks" in config:
        externalStacks = config["externalStacks"]
        for stack in externalStacks:
            for field in requiredFieldsExtStacks:
                if field not in stack:
                    raise RequiredExtStackFieldError(field, stack)

    # Checking that all Stack regions are supported by cloudformation
    session = boto3.session.Session()
    availableRegions = session.get_available_regions(service_name="cloudformation")
    for stack in (config["infrastructureTemplates"] + externalStacks):
        if stack["StackRegion"] not in availableRegions:
            raise UnsupportedRegionStackError(
                stack["StackRegion"], stack["StackName"], availableRegions)

    print("All required fields found in config file")


def checkFileExists(path):
    if os.path.isfile(path):
        print("File '%s' found" % (path))
    else:
        raise FileNotFoundError(path)


def checkIsJson(path):
    with open(path, 'r') as file:
        try:
            json.load(file)
            print("File '%s' content is valid Json" % (path))
        except ValueError:
            raise JsonFormatError(path)


def check_and_get_conf(conf):
    # checks every needed config and template files, and returns their
    # content
    checkConfigFile(conf)

    with open(conf, 'r') as configFile:
        config = json.load(configFile)

    # Changing working directory
    workDir = os.path.dirname(os.path.realpath(conf))
    os.chdir(workDir)
    print("Working directory is now : %s" % (workDir))

    print("Checking if infrastructure files exist and are valid")
    for template in config["infrastructureTemplates"]:
        checkFileExists(template["StackTemplate"])
        checkIsJson(template["StackTemplate"])

    print("Checking if task Def files exist")
    tasksDefsContent = {}
    for taskDefFile in config["taskDefsTemplates"]:
        checkFileExists(taskDefFile)
        checkIsJson(taskDefFile)
        taskDefName = taskDefFile.replace(
            "taskDef-", "").replace(".json", "")
        with open(taskDefFile) as f:
            tasksDefsContent[taskDefName] = json.load(f)

    print("Checking if service files exist")
    servicesContent = {}
    for serviceFile in config["servicesTemplates"]:
        checkFileExists(serviceFile)
        checkIsJson(serviceFile)
        serviceName = serviceFile.replace(
            "service-", "").replace(".json", "")
        with open(serviceFile) as f:
            servicesContent[serviceName] = json.load(f)

    # Getting config parameters
    configParams = {}
    configParams.update(config["globalParameters"])
    for template in config["infrastructureTemplates"]:
        configParams.update(template["StackParameters"])

    # Ordering templates according to the "StackOrder" field.
    # Cli will create them in a serial fashion, according to their
    # StackOrder.
    templates = config["infrastructureTemplates"]
    sortedTemplates = sorted(templates, key=lambda k: k['StackOrder'])
    config["infrastructureTemplates"] = sortedTemplates

    templates = []
    for template in config["infrastructureTemplates"]:
        with open(template["StackTemplate"]) as templateFile:
            templateContent = templateFile.read()
        templateTmp = template
        templateTmp["TemplateContent"] = templateContent
        templates.append(templateTmp)

    externalStacks = []
    if "externalStacks" in config:
        externalStacks = config["externalStacks"]

    return (config, configParams, templates,
            tasksDefsContent, servicesContent, externalStacks)


def mergeOutputConfig(stackOutput, configParams, stackTemplate):
    # Merge what is in stackOutput, and put it in configParams.
    # stackOutput and configParams are both dicts
    # If any key is in both dicts, this function will throw and error
    keys_configOutput = set(stackOutput.keys())
    keys_configParams = set(configParams.keys())
    intersection = keys_configOutput & keys_configParams
    if intersection != set():
        raise ConfigIntersectionError(stackTemplate, intersection)
    else:
        engine.dependencyResolver(target=configParams,
                                  resolve=True,
                                  valueSources=[stackOutput])
        configParams.update(stackOutput)


def verify_subset(stackSubset, templates):
    # Check that all stacks in subset are in the config file and
    # throw an error if a stack is not found
    # Check if there is a stack flagged with ComputeStack set
    # as true, if so return True
    ComputeStackFound = False
    for stack in stackSubset:
        stackFound = False
        for template in templates:
            if stack == template["StackName"]:
                stackFound = True
                if template["ComputeStack"].lower() == "true":
                    ComputeStackFound = True
                break
        if not stackFound:
            raise SubsetStackError(stack)
    return ComputeStackFound


def change_workdir(conf):
        # Changing working directory
    workDir = os.path.dirname(os.path.realpath(conf))
    os.chdir(workDir)
    print("Working directory is now : %s" % (workDir))
