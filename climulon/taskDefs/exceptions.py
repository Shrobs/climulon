from exceptions import UnresolvedDependency


class TaskDefUnresolvedDependency(UnresolvedDependency):

    def __init__(self, taskDef, missingRefs):
        self.message = ("ERROR : Unresolved dependencies for "
                        "TaskDef : %s\n" % (taskDef))
        super().__init__(missingRefs)
