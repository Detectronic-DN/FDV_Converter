import math
from src.calculator.calculator_exception import CalculatorException
from src.calculator.Calculator import Calculator
from src.calculator.wetted_area_helper import WettedAreaCalculationHelper


class Egg2Calculator(Calculator):
    """
    Calculator for a new type of egg-shaped cross-sections that computes flow values
    based on a single height parameter, with other dimensions derived from it.
    """

    def __init__(self, height: float):
        """
        Initializes a new instance of NewEggCalculator with the height of the
        egg-shaped cross-section.

        Args:
            height (float): The height of the egg-shaped cross-section.

        Raises:
            CalculatorException: If the height parameter is not a valid number.
        """
        if math.isnan(height):
            raise CalculatorException("Invalid Parameters Supplied to Constructor")

        self.height = height
        self.radius1 = height / 12.0
        self.radius2 = height / 3.0
        self.radius3 = 8.0 * height / 9.0
        self.offset = 5.0 * height / 9.0
        self.height2 = height - self.radius2
        self.height1 = self.height2 - self.radius3 * math.sin(
            math.atan((self.height2 - self.radius1) / self.offset)
        )

    def perform_calculation(self, depth, velocity) -> float:
        """
        Calculates the flow based on the depth and velocity using the egg-shaped
        cross-section dimensions derived from the height.

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
            self.height1,
            self.height2,
            self.offset,
            depth,
        )
        result = area * velocity * 1000.0
        return max(result, 0.0)
