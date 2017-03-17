import json
from exceptions import BasicException, UnresolvedDependency


class RequiredConfigFieldError(BasicException):

    def __init__(self, field):
        self.message = ("ERROR : Required field '%s' not found" % (field))


class RequiredTemplateFieldError(BasicException):

    def __init__(self, field, stack):
        self.message = ("ERROR : Required field '%s' missing for this "
                        "template\n" % (field))
        self.message += (json.dumps(stack, indent=3))

class RequiredExtStackFieldError(BasicException):

    def __init__(self, field, stack):
        self.message = ("ERROR : Required field '%s' missing for this "
                        "external stack\n" % (field))
        self.message += (json.dumps(stack, indent=3))


class FileNotFoundError(BasicException):

    def __init__(self, path):
        self.message = ("ERROR : File '%s' not found" % (path))


class JsonFormatError(BasicException):

    def __init__(self, path):
        self.message = ("ERROR : File '%s' content is not valid Json" % (path))


class ConfigIntersectionError(BasicException):

    def __init__(self, stackTemplate, intersection):
        self.message = ("ERROR : Conflict detected : Output in stack %s have "
                        "the same name as parameter in environment config "
                        "file \n" % (stackTemplate["StackName"]))
        self.message += ("Conflict parameters :\n")
        self.message += str(intersection)


class SubsetStackError(BasicException):

    def __init__(self, stack):
        self.message = ("ERROR : Stack \"%s\" not found in environment "
                        "config file" % (stack))


class StackDeletionError(BasicException):

    def __init__(self, stackName):
        self.message = ("ERROR : Stack %s deletion failed" % (stackName))


class ConcurrentDeployment(BasicException):

    def __init__(self, serviceArn):
        separator = "#######################################################"
        self.message = (separator)
        self.message += ("\nDeployment ID changed for service :\n")
        self.message += str(serviceArn)
        self.message += ("\nAnother build/deployment is running and "
                         "overriding this deployment")
        self.message += ("\n" + separator)


class ContainerDeploymentInstability(BasicException):

    def __init__(self, serviceArn, lastCount, currentCount):
        separator = "#######################################################"
        self.message = (separator)
        self.message += ("\nRunning container count dropped from "
                         "%s to %s for service :\n" %
                         (lastCount, currentCount))
        self.message += str(serviceArn)
        self.message += ("\nContainers are not stable and crashing on startup")
        self.message += ("\n" + separator)


class DeploymentTimeout(BasicException):

    def __init__(self, serviceARNs):
        separator = "#######################################################"
        self.message = (separator)
        self.message += ("\nDeployment timed out. Services that timed out:\n")
        self.message += str(serviceARNs)
        self.message += ("\n" + separator)


class ContainerRunningInstability(BasicException):

    def __init__(self, serviceARNs):
        separator = "#######################################################"
        self.message = (separator)
        self.message += ("\nContainer stability check timed out."
                         "Services that failed the check :\n")
        self.message += str(serviceARNs)
        self.message += ("\nContainers failed the Load balancer healthcheck "
                         "or are not responding")
        self.message += ("\n" + separator)


class StackExistsError(BasicException):

    def __init__(self, stackName):
        self.message = ("ERROR : There is already a CF stack with the name : "
                        "%s" % (stackName))


class TaskDefExistsError(BasicException):

    def __init__(self, taskDefName):
        self.message = ("ERROR : There is already a task definition "
                        "family named : %s" % (taskDefName))


class StackUnresolvedDependency(UnresolvedDependency):

    def __init__(self, stackName, missingRefs):
        self.message = ("ERROR : Unresolved dependencies for stack : %s\n"
                        % (stackName))
        super().__init__(missingRefs)


class EcrRepositoryError(BasicException):

    def __init__(self, repositoryName):
        self.message = ("ERROR : ECR repository not found"
                        " : %s" % (repositoryName))

class UnsupportedRegionStackError(BasicException):

    def __init__(self, region, stackName, possibleRegions):
        self.message = ("ERROR : Unsupported or non existant region for stack '%s'"
                        " : %s\n" % (stackName, region))
        self.message += ("Choose from one of these regions :\n")
        self.message += str(possibleRegions)

class UnsupportedRegionError(BasicException):

    def __init__(self, region, possibleRegions):
        self.message = ("ERROR : Unsupported or non existant region for the ECR service"
                        " : %s" % (region))
        self.message += ("Choose from one of these regions :\n")
        self.message += str(possibleRegions)

class WrongFieldFormat(BasicException):

    def __init__(self, imageArg):
        self.message = ("ERROR : Argument needs to be in the format : key=value\n")
        self.message += ("Offending argument : %s" % imageArg)

class NotADockerImageName(BasicException):

    def __init__(self, image):
        self.message = ("ERROR : Not a correct docker image name : %s" % (image))

class ExternalStackNotFound(BasicException):

    def __init__(self, stackName):
        self.message = ("ERROR : External stack \"%s\" not found" % (stackName))

class StackNotFound(BasicException):

    def __init__(self, stackName):
        self.message = ("ERROR : Stack \"%s\" not found" % (stackName))

