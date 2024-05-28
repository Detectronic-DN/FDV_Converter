import math


def R3Calculator(w: float, h: float, eggForm: int) -> float:
    """
    Calculate the radius r3 for a given width (w), height (h), and egg shape type (eggForm).
    Returns the calculated radius or -1.0 if an error occurs (e.g., non-convergence or math domain error).
    """
    iterations: int = 0
    max_iterations: int = 1000
    precision: float = 1e-5
    r2: float = w / 2.0

    r1: float = (h - w) / (2.0 if eggForm == 1 else 4.0)
    h2: float = h - r2
    r3: float = h
    diff: float = 1.0

    while abs(diff) > precision and iterations < max_iterations:
        offset: float = r3 - r2
        square_term: float = (r3 - r1) ** 2 - (h2 - r1) ** 2

        if square_term < 0:
            print("Math domain error: the value inside the square root is negative.")
            return -1

        offsetA: float = math.sqrt(square_term)
        diff = offset - offsetA

        r3 += diff / 10.0
        iterations += 1

    if iterations >= max_iterations:
        print("Failed to converge within the maximum number of iterations.")
        return -1

    return r3
