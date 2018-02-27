from sqlalchemy.sql.elements import ColumnClause


class ColumnReference(ColumnClause):
    """ Column reference used to detect that path resolution is required. """

    def unique_params(self, *optionaldict, **kwargs):
        raise NotImplementedError("Immutable objects do not support copying")

    def params(self, *optionaldict, **kwargs):
        raise NotImplementedError("Immutable objects do not support copying")

    def __init__(self, text):
        super(ColumnReference, self).__init__(text, is_literal=True)


def ref(text):
    """ Generate column reference for custom filtering logic. """
    return ColumnReference(text)
