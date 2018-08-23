from abc import abstractmethod


class AbstractType():
    @abstractmethod
    def validator(self, attr_name):
        raise NotImplementedError()
