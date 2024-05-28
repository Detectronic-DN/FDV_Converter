import math
from typing import List


class WettedAreaCalculationHelper:
    """
    Helper class for calculating the wetted area and perimeter of an egg-shaped channel.
    """

    @staticmethod
    def area(
        height: float,
        radius1: float,
        radius2: float,
        radius3: float,
        h1: float,
        h2: float,
        offset: float,
        depth_of_water: float,
    ) -> List[float]:
        """
        Calculates the wetted area and perimeter of the egg-shaped channel based on the given dimensions and depth.

        Args:
            height (float): The height of the channel.
            radius1, radius2, radius3 (float): The radii defining the egg shape.
            h1, h2 (float): Heights at different sections of the egg shape.
            offset (float): The horizontal offset in the egg shape.
            depth_of_water (float): The depth of water in the channel.

        Returns:
            List[float]: A list containing the calculated wetted area and perimeter.
        """
        wetted_area = 0.0
        perimeter = 0.0
        if depth_of_water > height * 0.9999:
            depth_of_water = height * 0.9999
        psi = math.atan((h2 - radius1) / offset)
        area1 = 0.25 * math.pow(radius3, 2.0) * (2.0 * psi - math.sin(2.0 * psi))
        inner_rect = math.sqrt(math.pow(radius1, 2.0) - math.pow(radius1 - h1, 2.0))

        if depth_of_water <= h1:
            theta = 2.0 * math.acos((radius1 - depth_of_water) / radius1)
            wetted_area = 0.5 * (theta - math.sin(theta)) * math.pow(radius1, 2.0)
            perimeter = 2.0 * radius1 * math.acos((radius1 - depth_of_water) / radius1)
        elif h1 < depth_of_water <= h2:
            z = h2 - depth_of_water
            phi = math.asin(z / radius3)
            area2 = 0.25 * math.pow(radius3, 2.0) * (2.0 * phi - math.sin(2.0 * phi))
            x1 = math.sqrt(math.pow(radius3, 2.0) - math.pow(z, 2.0))
            m = depth_of_water - h1
            p = x1 - offset - inner_rect
            area3 = m * inner_rect
            area4 = p * (h2 - depth_of_water)
            area5 = area1 - area2 - area4
            theta = 2.0 * math.acos((radius1 - h1) / radius1)
            area_lower_segment = (
                0.5 * (theta - math.sin(theta)) * math.pow(radius1, 2.0)
            )
            wetted_area = area_lower_segment + 2.0 * (area5 + area3)
            alpha = psi - phi
            perimeter2 = radius3 * alpha * 2.0
            perimeter3 = 2.0 * radius1 * math.acos((radius1 - h1) / radius1)
            perimeter = perimeter3 + perimeter2
        elif depth_of_water > h2:
            i = depth_of_water - h1
            area6 = i * inner_rect
            area7 = area1
            area_middle_segment = 2.0 * (area7 + area6)
            theta = 2.0 * math.acos((radius1 - h1) / radius1)
            area_lower_segment2 = (
                0.5 * (theta - math.sin(theta)) * math.pow(radius1, 2.0)
            )
            area8 = math.pi * radius2 * radius2 / 2.0
            z = depth_of_water - h2 + radius2
            z = radius2 * 2.0 - z
            gamma = 2.0 * math.acos((radius2 - z) / radius2)
            area9 = (
                math.pi * radius2 * radius2
                - radius2 * radius2 * (gamma - math.sin(gamma)) / 2.0
            )
            area_upper_segment = area9 - area8
            perimeter4 = math.pi * radius2 - radius2 * gamma
            wetted_area = area_lower_segment2 + area_middle_segment + area_upper_segment
            alpha2 = psi
            perimeter5 = radius3 * alpha2 * 2.0
            perimeter6 = 2.0 * radius1 * math.acos((radius1 - h1) / radius1)
            perimeter = perimeter6 + perimeter5 + perimeter4

        return wetted_area, perimeter
