
class MapColumn(dict):
    """ Dictionary Column defining custom hierarchies """
    def __init__(self, seq=None, **kwargs):
        # handle direct mappings
        if isinstance(seq, (list, str)):
            seq = {None: seq}
        super(MapColumn, self).__init__(seq, **kwargs)
