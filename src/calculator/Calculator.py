from abc import ABC, abstractmethod


class Calculator(ABC):
    @abstractmethod
    def perform_calculation(self, depth, velocity):
        pass
        # raise NotImplementedError("This method should be overridden by subclasses.")
