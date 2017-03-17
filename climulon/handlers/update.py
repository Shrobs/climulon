import boto3
from handlers import utils
import dependency_engine as engine
from handlers.exceptions import (ExternalStackNotFound,
                                 StackNotFound)


def update_handler(args):
    # Handler for infra templates update
    conf = args.conf
    stackSubset = args.stacks
    timeout = args.timeout
    if timeout is None:
        timeout = 60
    dry_run = args.dry_run
    changeset_name = args.changeset_name
    autoYes = args.yes
    run_provision(conf, stackSubset, timeout, dry_run, autoYes)


def run_update(conf, stackSubset, timeout, dry_run, autoYes):
    (config, configParams, templates, tasksDefsContent,
     servicesContent, externalStacks) = utils.check_and_get_conf(conf)

    if stackSubset:
        print("Stack list detected, will only update this sub-set "
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

    # Checking that all the stacks to be updated exist
    print("Checking if the stacks that are marked for update exist")
    for template in templates:
        if template["StackName"] in stackSubset:
            client = boto3.client('cloudformation', region_name=template["StackRegion"])
            try:
                response = client.describe_stacks(StackName=template["StackName"])
            except botocore.exceptions.ClientError as e:
                if (e.response['Error']['Code'] ==
                        'ValidationError' and
                        "does not exist" in
                        e.response['Error']['Message']):
                    raise StackNotFound(template["StackName"])
                else:
                    raise

    print("Checks complete, preparing approximative update plan")


