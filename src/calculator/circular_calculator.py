import math
from src.calculator.calculator_exception import CalculatorException
from src.calculator.Calculator import Calculator


class CircularCalculator(Calculator):
    """
    Calculator for circular pipes that computes flow values based on pipe radius,
    depth value, and velocity value.
    """

    def __init__(self, pipe_radius: float):
        """
        Initializes a new instance of the CircularCalculator class.

        Args:
            pipe_radius (float): The radius of the pipe.

        Raises:
            CalculatorException: If the provided pipe radius is not a valid number (NaN).
        """
        self.pipe_radius = 0.0
        self.radius_squared = 0.0
        self.circle_area = 0.0

        if math.isnan(pipe_radius):
            raise CalculatorException("Pipe Radius Invalid.")

        self.pipe_radius = pipe_radius
        self.radius_squared = pipe_radius**2
        self.circle_area = math.pi * self.radius_squared

    def calculate_flow_value(self, depth_value: float, velocity_value: float) -> float:
        """
        Calculates the flow value based on the depth and velocity of the water in the pipe.

        Args:
            depth_value (float): The depth of the water in the pipe.
            velocity_value (float): The velocity of the water flow in the pipe.

        Returns:
            float: The calculated flow value.
        """
        if depth_value > self.pipe_radius:
            if depth_value < self.pipe_radius * 2.0:
                t = depth_value - self.pipe_radius
                chord_length = 2.0 * math.sqrt(self.radius_squared - t**2)
                c = chord_length / 2.0
                interior_angle = 2.0 * math.atan(c / t)
                segment_area = (
                    self.radius_squared
                    * (interior_angle - math.sin(interior_angle))
                    / 2.0
                )
                return (self.circle_area - segment_area) * velocity_value * 1000.0
            return self.circle_area * velocity_value * 1000.0
        else:
            if depth_value == self.pipe_radius:
                return self.circle_area / 2.0 * velocity_value * 1000.0
            if depth_value > 0.0:
                t = self.pipe_radius - depth_value
                chord_length = 2.0 * math.sqrt(self.radius_squared - t**2)
                c = chord_length / 2.0
                interior_angle = 2.0 * math.atan(c / t)
                segment_area = (
                    self.radius_squared
                    * (interior_angle - math.sin(interior_angle))
                    / 2
                )
                return segment_area * velocity_value * 1000.0
            return 0.0

    def perform_calculation(self, depth, velocity):
        """
        Performs the calculation as defined by the Calculator abstract base class.
        This method is intended to be used to calculate flow value based on provided inputs.
        """

        return self.calculate_flow_value(depth, velocity)
