import math

from src.calculator.Calculator import Calculator


def calculate_segment_area(radius: float, height: float) -> float:
    """
    Calculates the area of a circle segment based on the radius of the circle and
    the height of the segment.

    Args:
        radius (float): The radius of the circle.
        height (float): The height of the segment from the base of the circle.

    Returns:
        float: The area of the circle segment.
    """
    radius_squared = radius ** 2
    t = radius - height
    chord_length = 2.0 * math.sqrt(radius_squared - t ** 2)
    c = chord_length / 2.0
    interior_angle = 2.0 * math.atan(c / t)
    segment_area = (
            radius_squared * (interior_angle - math.sin(interior_angle)) / 2.0
    )
    return segment_area


class TwoCircleAndRectangleCalculator(Calculator):
    """
    Calculator for a flow channel with a cross-section composed of two half-circles
    and a rectangle, calculating flow based on depth and velocity.
    """

    def __init__(self, width: float, height: float):
        """
        Initializes a new instance of the TwoCircleAndRectangleCalculator with the
        dimensions of the channel.

        Args:
            width (float): The width of the rectangular part of the channel.
            height (float): The total height of the channel, including half-circles.
        """
        self.height = height
        self.width = width

    def perform_calculation(self, depth, velocity) -> float:
        """
        Calculates the flow based on the depth and velocity of the fluid, taking into
        account the specific cross-sectional shape of the channel.

        Args:
            velocity:
            depth:

        Returns:
            float: The calculated flow.
        """
        r1 = self.width / 2.0
        d = depth
        v = velocity
        radius_squared = r1 ** 2
        circle_area = math.pi * radius_squared

        if d < r1:
            return calculate_segment_area(r1, d) * v * 1000.0 if d > 0 else 0.0
        elif d < self.height - r1:
            d -= r1
            rectangle_area = d * self.width
            bottom_half_circle_area = circle_area / 2.0
            return (bottom_half_circle_area + rectangle_area) * v * 1000.0
        elif d < self.height:
            d = d - self.width / 2.0 - (self.height - self.width)
            top_half_circle_area = circle_area / 2.0 - calculate_segment_area(
                r1, r1 - d
            )
            rectangle_area2 = (self.height - self.width) * self.width
            bottom_half_circle_area2 = circle_area / 2.0
            return (
                    (bottom_half_circle_area2 + rectangle_area2 + top_half_circle_area)
                    * v
                    * 1000.0
            )
        else:
            top_half_circle_area = circle_area / 2.0
            rectangle_area2 = (self.height - self.width) * self.width
            bottom_half_circle_area2 = circle_area / 2.0
            return (
                    (bottom_half_circle_area2 + rectangle_area2 + top_half_circle_area)
                    * v
                    * 1000.0
            )
