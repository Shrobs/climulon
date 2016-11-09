import boto3
import botocore
import time
from handlers import utils
from handlers.exceptions import (ConcurrentDeployment,
                                 ContainerDeploymentInstability,
                                 DeploymentTimeout,
                                 ContainerRunningInstability)


def status_handler(args):
    # Handler for deployment status check using infra templates
    conf = args.conf
    deploymentTimeout = args.deploymentTimeout
    stabilityTimeout = args.stabilityTimeout
    tick = args.tick
    run_status(conf, deploymentTimeout, stabilityTimeout, tick)


def run_status(conf, deploymentTimeout, stabilityTimeout, tick):
    (config, configParams, templates, tasksDefsContent,
     servicesContent) = utils.check_and_get_conf(conf)

    utils.change_workdir(conf)

    ComputeStackFound = False
    for template in templates:
        if template["ComputeStack"].lower() == "true":
            client = boto3.client('cloudformation', 
                                  region_name=template["StackRegion"])
            try:
                client.describe_stacks(StackName=template["StackName"])
                print("Stack with ComputeStack flag set to 'true' found "
                      ": %s" % (template["StackName"]))
                ComputeStackFound = True
                ComputeStackRegion = template["StackRegion"]
            except botocore.exceptions.ClientError as e:
                if (e.response['Error']['Code'] ==
                        'ValidationError' and
                        "does not exist" in
                        e.response['Error']['Message']):
                    pass
                else:
                    print(e)

    if not ComputeStackFound:
        print("ERROR : No stack with ComputeStack set as True is "
              "currently running, cannot check deployment")

    client = boto3.client('ecs', region_name=ComputeStackRegion)

    # Getting current cluster services
    services = client.list_services(
        cluster=configParams["EcsClusterName"])
    print("Services to be checked :")
    for service in services["serviceArns"]:
        print(service)
    serviceARNs = services["serviceArns"]

    print("Checking deployment status")
    timer = 0
    firstLoop = True
    servicesDeploymentIds = {}
    servicesContainerCount = {}
    while timer <= deploymentTimeout and serviceARNs != []:
        serviceDesc = client.describe_services(
            cluster=configParams["EcsClusterName"],
            services=serviceARNs
        )
        for service in serviceDesc["services"]:
            print("Checking deployment for service : %s" %
                  (service["serviceName"]))
            # Saving the original primary deployment ID for every service
            if firstLoop:
                for deployment in service["deployments"]:
                    if deployment["status"] == "PRIMARY":
                        servicesDeploymentIds[
                            service["serviceName"]] = deployment["id"]
                servicesContainerCount[service["serviceName"]] = 0
            for deployment in service["deployments"]:
                if deployment["status"] == "PRIMARY":
                    # If deployment ID changes, that means another
                    # build/deployment is running
                    if (not firstLoop and
                            deployment["id"] != servicesDeploymentIds[
                            service["serviceName"]]):
                        raise ConcurrentDeployment(service["serviceArn"])
                    # If running containers count is lower than last loop,
                    # that means that containers are crashing
                    elif (deployment["runningCount"] <
                          servicesContainerCount[service["serviceName"]]):
                        currentCount = servicesContainerCount[
                            service["serviceName"]]
                        raise ContainerDeploymentInstability(
                            service["serviceArn"],
                            currentCount,
                            deployment["runningCount"])
                    elif (deployment["runningCount"] ==
                            deployment["desiredCount"]):
                        print("Service deployed successfully : %s" %
                              (service["serviceName"]))
                        serviceARNs.remove(service["serviceArn"])
                    else:
                        print("Service %s not yet fully deployed : "
                              "Running count (%s) Desired count (%s)" %
                              (service["serviceName"],
                               deployment["runningCount"],
                               deployment["desiredCount"]
                               ))
                        servicesContainerCount[
                            service["serviceName"]
                        ] = deployment["runningCount"]
        if serviceARNs != []:
            time.sleep(tick)
            timer = timer + tick
        if firstLoop:
            firstLoop = False

    if serviceARNs != []:
        raise DeploymentTimeout(serviceARNs)

    print("Checking containers' stability")
    services = client.list_services(
        cluster=configParams["EcsClusterName"])
    serviceARNs = services["serviceArns"]
    serviceDesc = client.describe_services(
        cluster=configParams["EcsClusterName"],
        services=serviceARNs
    )

    timer = 0
    while timer <= stabilityTimeout and serviceARNs != []:
        serviceDesc = client.describe_services(
            cluster=configParams["EcsClusterName"],
            services=serviceARNs
        )
        for service in serviceDesc["services"]:
            print("Checking containers for service : %s" %
                  (service["serviceName"]))
            if ("has reached a steady state" in
                    service["events"][0]["message"]):
                print("Containers are stable for : %s" %
                      (service["serviceName"]))
                serviceARNs.remove(service["serviceArn"])
            else:
                print("Containers not yet stable for : %s" %
                      (service["serviceName"]))
        if serviceARNs != []:
            time.sleep(tick)
            timer = timer + tick

    if serviceARNs != []:
        raise ContainerRunningInstability(serviceARNs)
