from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker
from painless_sqlalchemy.core.ModelRaw import ModelRaw


class ModelAction(ModelRaw):
    """ ORM Action Abstraction """

    __abstract__ = True

    def __init__(self, **kwargs):
        super(ModelAction, self).__init__()
        self.update(**kwargs)

    def _get_session(self):
        """
            Get current Session for Instance or create new Session
            :return valid session
        """
        session = Session.object_session(self)
        if not session:
            session = sessionmaker(bind=self.engine)()
        return session

    def save(self):
        """
            Save model to database
            :return saved model
        """
        session = self._get_session()
        session.add(self)
        session.commit()
        return self

    def delete(self):
        """
            Delete model from database
            :return deleted model
        """
        session = self._get_session()
        session.delete(self)
        session.commit()
        return self

    def update(self, **kwargs):
        """
            Update model attributes without flushing
            :return updated, dirty model
        """
        inspected = inspect(self.__class__)
        all_cols = inspected.column_attrs.keys()
        all_rels = inspected.relationships.keys()
        all_cols_and_rels = all_cols + all_rels
        for key, value in kwargs.items():
            if key not in all_cols_and_rels:
                raise AttributeError("Key \"%s\" is not a valid column." % key)
            setattr(self, key, value)
        return self

    def rollback(self):
        """
            Roll back attached session
            :return model
        """
        self._get_session().rollback()
        return self
