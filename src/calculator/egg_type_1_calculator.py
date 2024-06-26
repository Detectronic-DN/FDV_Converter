import math

from src.calculator.Calculator import Calculator
from src.calculator.calculator_exception import CalculatorException
from src.calculator.wetted_area_helper import WettedAreaCalculationHelper


class Egg1Calculator(Calculator):
    """
    Calculator for egg-shaped cross-sections in channels, computing flow values based on
    given dimensions and properties of the egg shape.
    """

    def __init__(self, width: float, height: float, radius3: float):
        """
        Initializes a new instance of the EggCalculator class.

        Args:
            width (float): The width of the egg-shaped cross-section.
            height (float): The height of the egg-shaped cross-section.
            radius3 (float): The radius of the bottom part of the egg shape.

        Raises:
            CalculatorException: If any of the parameters are NaN or invalid.
        """
        if math.isnan(width) or math.isnan(height) or math.isnan(radius3):
            raise CalculatorException("Invalid Parameters Supplied to Constructor")

        self.height = height
        self.radius1 = (height - width) / 2.0
        self.radius2 = width / 2.0
        self.radius3 = radius3
        self.offset = radius3 - self.radius2
        self.height2 = height - self.radius2
        self.height1 = self.height2 - radius3 * math.sin(
            math.atan((self.height2 - self.radius1) / self.offset)
        )

    def perform_calculation(self, depth, velocity) -> float:
        """
        Calculates the flow based on the depth and velocity using the egg-shaped cross-section dimensions.

        Args:
            velocity:
            depth:

        Returns:
            float: The calculated flow value or 0.0 if the result is not a number.

        Raises:
            CalculatorException: If the number of inputs is not 2.
        """
        area, _ = WettedAreaCalculationHelper.area(
            self.height,
            self.radius1,
            self.radius2,
            self.radius3,
            self.height1,
            self.height2,
            self.offset,
            depth,
        )
        result = velocity * area * 1000.0
        return max(result, 0.0)
