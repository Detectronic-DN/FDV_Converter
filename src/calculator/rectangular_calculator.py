import math
from src.calculator.calculator_exception import CalculatorException
from src.calculator.Calculator import Calculator


class RectangularCalculator(Calculator):
    """
    Calculator for rectangular channels that computes flow values based on channel width,
    depth value, and velocity value.
    """

    def __init__(self, width: float):
        """
        Initializes a new instance of the RectangularCalculator class.

        Args:
            width (float): The width of the channel.

        Raises:
            CalculatorException: If the provided channel width is not a valid number (NaN).
        """
        self.channel_width = 0.0

        if math.isnan(width):
            raise CalculatorException("Channel Width Invalid.")

        self.channel_width = width

    def perform_calculation(self, depth, velocity) -> float:
        """
        Performs the calculation as defined by the Calculator abstract base class.
        This method calculates the flow value based on depth, velocity, and channel width.

        Args:
            inputs (List[float]): A list containing two floats: depth value and velocity value.

        Returns:
            float: The result of the calculation, or 0.0 if the calculated flow is negative.

        Raises:
            CalculatorException: If the number of inputs provided is not equal to 2.
        """
        flow = depth * velocity * self.channel_width * 1000.0
        return max(flow, 0.0)
