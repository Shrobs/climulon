import boto3
import json
import dependency_engine as engine
from services.exceptions import ServiceUnresolvedDependency


def fill_service_templates(servicesContent, configParams):
    # Filling service templates with variables
    print("Filling service templates with parameters...")
    for service in servicesContent:
        print("Updating service : %s" % (service))
        missingRefs = engine.dependencyResolver(
            servicesContent[service], resolve=True,
            valueSources=[configParams])
        if missingRefs:
            raise ServiceUnresolvedDependency(service, missingRefs)
        servicesContent[service] = json.dumps(servicesContent[service])
        print("Service updated : %s" % (service))
    return servicesContent


def create_services(servicesContent, region):
    # Creating services
    client = boto3.client('ecs', region_name=region)
    print("Creating services...")
    for service in servicesContent:
        print("Creating service : %s" % (service))
        template = json.loads(servicesContent[service])
        serviceCreateResponse = client.create_service(
            cluster=template["cluster"],
            serviceName=template["serviceName"],
            taskDefinition=template["taskDefinition"],
            loadBalancers=template["loadBalancers"],
            desiredCount=template["desiredCount"],
            role=template["role"],
            deploymentConfiguration=template["deploymentConfiguration"]
        )
        print("Service created : %s" %
              (serviceCreateResponse["service"]["serviceArn"]))


def update_services(servicesContent, region):
    # Updating services
    client = boto3.client('ecs', region_name=region)
    print("Updating services...")
    for service in servicesContent:
        print("Updating service : %s" % (service))
        template = json.loads(servicesContent[service])
        serviceUpdateResponse = client.update_service(
            cluster=template["cluster"],
            service=template["serviceName"],
            desiredCount=template["desiredCount"],
            taskDefinition=template["taskDefinition"],
            deploymentConfiguration=template["deploymentConfiguration"]
        )
        print("Service updated : %s" %
              (serviceUpdateResponse["service"]["serviceArn"]))
