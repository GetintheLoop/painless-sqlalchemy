def flatten_dict(input_, prefix=None, join_with=".", filter_none=True):
    """ Flatten a dictionary """
    if prefix is None:
        prefix = []
    if isinstance(input_, list):
        result = {}
        for v in input_:
            result.update(flatten_dict(v, prefix, join_with, filter_none))
        return result
    if isinstance(input_, dict):
        result = {}
        for k, v in input_.items():
            prefix.append(k)
            result.update(flatten_dict(v, prefix, join_with, filter_none))
            prefix.pop()
        return result
    if filter_none is True and input_ is None:
        return {}
    return {join_with.join(prefix): input_}
