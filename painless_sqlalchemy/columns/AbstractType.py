from abc import abstractmethod


class AbstractType(object):
    @abstractmethod
    def validator(self, attr_name):
        raise NotImplementedError()
