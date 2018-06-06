from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.dialects import postgresql
from painless_sqlalchemy.core.Model import Model


def many_to_many(from_col, to_col, from_uuid=False, to_uuid=False,
                 from_cascade=None, to_cascade=None,
                 extra_cols=None, cascade=False, self_join=False):
    """ Generate many to many relationship table """
    if cascade:
        from_cascade = cascade if from_cascade is None else from_cascade
        to_cascade = cascade if to_cascade is None else to_cascade
    data = [
        '%s_to_%s' % (from_col, to_col),
        Model.metadata,
        Column(
            '%s%s_id' % ("" if self_join is False else "left_", from_col),
            postgresql.UUID if from_uuid else Integer,
            ForeignKey('%s.id' % from_col, ondelete='cascade' if from_cascade else None),
            primary_key=True
        ),
        Column(
            '%s%s_id' % ("" if self_join is False else "right_", to_col),
            postgresql.UUID if to_uuid else Integer,
            ForeignKey('%s.id' % to_col, ondelete='cascade' if to_cascade else None),
            primary_key=True
        )
    ]
    if extra_cols is not None:
        data += extra_cols
    return Table(*data)
