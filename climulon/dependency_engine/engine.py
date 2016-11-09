def dependencyResolver(target, resolve=False, valueSources=None):
    # Recursive function. Looks through a dict and into its nested dicts
    # and lists for any dict with this format {"Ref":"foobar"} and calls a
    # function thats replaces it with the value of the parameter with the
    # name "foobar"
    # Target : is the dict where Ref values are gonna be resolved
    # resolve : True to resolved Ref values and reporte non resolved values
    #           False to just report non resolved values
    # ValuesSource : Params that are gonna be set for the target's Ref
    #                values
    unresolvedDependencies = []
    if isinstance(target, dict):
        for k, v in target.items():
            if isinstance(v, dict):
                if list(v.keys()) == ["Ref"]:
                    SubstituteValue = None
                    if resolve:
                        SubstituteValue = getRefValue(
                            v["Ref"], valueSources)
                    if SubstituteValue is not None:
                        target[k] = SubstituteValue
                    else:
                        unresolvedDependencies.append(v["Ref"])
                else:
                    missingDep = dependencyResolver(
                        v, resolve, valueSources)
                    unresolvedDependencies += missingDep
            elif isinstance(v, list):
                missingDep = dependencyResolver(
                    v, resolve, valueSources)
                unresolvedDependencies += missingDep
    if isinstance(target, list):
        for v in target:
            if isinstance(v, (dict, list)):
                missingDep = dependencyResolver(
                    v, resolve, valueSources)
                unresolvedDependencies += missingDep
    return unresolvedDependencies


def getRefValue(ref, valueSources):
    if valueSources is not None:
        for source in valueSources:
            for key in source:
                if key == ref:
                    return source[key]
    return None
