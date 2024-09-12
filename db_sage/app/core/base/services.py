from abc import ABC, abstractmethod

class Service(ABC):
    """Base class model for database operations

    Args:
        ABC: helper class that provides a standard way to create an ABC using
inheritance
    """
    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def fetch(self):
        pass

    @abstractmethod
    def fetch_all(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def delete(self):
        pass