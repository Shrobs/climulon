from exceptions import UnresolvedDependency


class ServiceUnresolvedDependency(UnresolvedDependency):

    def __init__(self, service, missingRefs):
        self.message = ("ERROR : Unresolved dependencies for "
                        "service : %s\n" % (service))
        super().__init__(missingRefs)
