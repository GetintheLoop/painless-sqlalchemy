from painless_sqlalchemy.BaseModel import Base, engine


def get_tables():
    """
        List defined database tables.
    :return: A list of table names
    """
    return {t.name: t for t in Base.metadata.tables.values()}


def get_dump():
    """
        Get a database dump (for comparison purposes only)
    :return: A database dump
    """
    result = []

    tables = get_tables()
    for tbl in tables:
        data = engine.execute(tables[tbl].select()).fetchall()
        for a in data:
            result.append("%s %s" % (
                tbl,
                ", ".join("%s=%s" % v for v in zip([
                    c.name for c in tables[tbl].columns
                ], a))
            ))
    return result
