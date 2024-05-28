import math
from src.calculator.calculator_exception import CalculatorException
from src.calculator.Calculator import Calculator
from src.calculator.wetted_area_helper import WettedAreaCalculationHelper


class Egg2ACalculator(Calculator):
    """
    Calculator for a new type of egg-shaped cross-sections, specifically designed
    to compute flow values based on given dimensions.
    """

    def __init__(self, height: float, width: float, radius3: float):
        """
        Initializes a new instance of NewEggACalculator with height, width,
        and the third radius of the egg-shaped cross-section.

        Args:
            height (float): The height of the egg-shaped cross-section.
            width (float): The width of the egg-shaped cross-section.
            radius3 (float): The radius of the bottom part of the egg shape.
        """
        self.height = self.radius1 = self.radius2 = self.radius3 = 0.0
        self.h1 = self.h2 = self.offset = 0.0
        self.height = height
        self.radius1 = (height - width) / 4.0
        self.radius2 = width / 2.0
        self.radius3 = radius3
        self.offset = self.radius3 - self.radius2
        self.h2 = self.height - self.radius2
        self.h1 = self.h2 - self.radius3 * math.sin(
            math.atan((self.h2 - self.radius1) / self.offset)
        )

    def perform_calculation(self, depth, velocity) -> float:
        """
        Calculates the flow based on the depth and velocity using the new egg-shaped cross-section.

        Args:
            inputs (List[float]): A list containing the depth of water and velocity.

        Returns:
            float: The calculated flow value or 0.0 if the result is not a number.

        Raises:
            CalculatorException: If the number of inputs provided is not equal to 2.
        """
        area, _ = WettedAreaCalculationHelper.area(
            self.height,
            self.radius1,
            self.radius2,
            self.radius3,
            self.h1,
            self.h2,
            self.offset,
            depth,
        )
        result = area * velocity * 1000.0
        return max(result, 0.0)
