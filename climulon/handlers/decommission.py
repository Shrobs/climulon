import boto3
import botocore
import time
from handlers import utils
from handlers.exceptions import StackDeletionError


def decommission_handler(args):
    # Handler for both codeship and regular cli, for decommissioning stacks
    conf = args.conf
    stackSubset = args.stacks
    run_decommission(conf, stackSubset)


def run_decommission(conf, stackSubset):
    (config, configParams, templates, tasksDefsContent,
     servicesContent) = utils.check_and_get_conf(conf)

    if stackSubset:
        print("Stack list detected, will only decommission this sub-set "
              "of stacks :")
        print(stackSubset)
    else:
        stackSubset = []
        for template in templates:
            stackSubset.append(template["StackName"])

    ComputeStackFound = utils.verify_subset(stackSubset, templates)

    print("Deleting cloudformation stack...")

    for template in reversed(templates):
        if template["StackName"] in stackSubset:
            print("Deleting stack : %s" % (template["StackName"]))
            client = boto3.client('cloudformation', region_name=template["StackRegion"])
            client.delete_stack(
                StackName=template["StackName"]
            )

            while True:
                try:
                    describeStackResponse = client.describe_stacks(
                        StackName=template["StackName"])
                except botocore.exceptions.ClientError as e:
                    if (e.response['Error']['Code'] ==
                            'ValidationError' and
                            "does not exist" in
                            e.response['Error']['Message']):
                        print("Stack deletion complete")
                        break
                stack = describeStackResponse["Stacks"][0]
                if (stack["StackStatus"] == 'DELETE_FAILED'):
                    raise StackDeletionError(template["StackName"])
                elif stack["StackStatus"] == 'DELETE_COMPLETE':
                    print("Stack deletion complete")
                    break
                else:
                    print("Stack deletion in progress")
                    time.sleep(20)

            if template["ComputeStack"].lower() == "true":
                print("Deregistering task definitions...")
                client = boto3.client('ecs', region_name=template["StackRegion"])
                for key, value in config["globalParameters"].items():
                    if "TASK_DEF_NAME" in key:
                        taskDefRevs = client.list_task_definitions(
                            familyPrefix=value,
                            status="ACTIVE"
                        )
                        for revArn in taskDefRevs["taskDefinitionArns"]:
                            client.deregister_task_definition(
                                taskDefinition=revArn
                            )
                print("Task definitions deregistered")

                print("Deleting services...")
                getServicesResponse = client.list_services(
                    cluster=configParams["EcsClusterName"],
                )
                servicesList = getServicesResponse["serviceArns"]
                for service in servicesList:
                    # Getting service desired count to 0
                    client.update_service(
                        cluster=configParams["EcsClusterName"],
                        service=service,
                        desiredCount=0
                    )
                    # Deleting service
                    client.delete_service(
                        cluster=configParams["EcsClusterName"],
                        service=service
                    )
                print("Services deleted")

                print("Deleting ECS cluster...")
                client.delete_cluster(
                    cluster=configParams["EcsClusterName"]
                )
                print("ECS cluster deleted")

    print("Decommission complete")
