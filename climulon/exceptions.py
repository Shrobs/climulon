class BasicException(Exception):
    pass


class UnresolvedDependency(BasicException):
    message = ""

    def __init__(self, missingRefs):
        self.message += ("Unresolved dependencies :\n")
        self.message += str(missingRefs)
