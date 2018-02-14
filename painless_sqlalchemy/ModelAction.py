from sqlalchemy import inspect
from sqlalchemy.orm import Session
from painless_sqlalchemy.ModelBase import ModelBase


class ModelAction(ModelBase):
    """ Simplified Actions for Instance """

    def _get_session(self):
        """
            Get the current session for this object.
            :return: a valid session
        """
        return Session.object_session(self)

    def save(self):
        """
            Save model to the database.
            :return: the model
        """
        session = self._get_session()
        session.add(self)
        session.commit()
        return self

    def delete(self):
        """
            Delete model from the database.
            :return: the now deleted model
        """
        session = self._get_session()
        session.delete(self)
        session.commit()
        return self

    def update(self, **kwargs):
        """ Update this db objects attributes with given kwargs. """
        inspected = inspect(self.__class__)
        all_cols = inspected.column_attrs.keys()
        all_rels = inspected.relationships.keys()
        all_cols_and_rels = all_cols + all_rels
        for key, value in kwargs:
            if key not in all_cols_and_rels:
                raise AttributeError("Key \"%s\" is not a valid column." % key)
            setattr(self, key, value)
        return self

    def rollback(self):
        """ Roll back the session attached to this object. """
        self._get_session().rollback()
