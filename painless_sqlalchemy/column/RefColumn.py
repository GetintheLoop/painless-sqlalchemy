from sqlalchemy.sql.elements import ColumnClause


class RefColumn(ColumnClause):
    """ Generate reference column for custom filtering logic. """

    def __init__(self, text):
        super(RefColumn, self).__init__(text, is_literal=True)
