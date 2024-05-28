import pandas as pd
from src.calculator.egg_type_1_calculator import Egg1Calculator
from src.calculator.egg_type_2a_calculator import Egg2ACalculator
from src.calculator.egg_type_2_calculator import Egg2Calculator
from src.calculator.circular_calculator import CircularCalculator
from src.calculator.rectangular_calculator import RectangularCalculator
from src.calculator.circle_and_rectangle import TwoCircleAndRectangleCalculator
from src.FDV.FDV_flow_creator import FDVFlowCreator


def FDV_conversion(
    csv_file_name,
    output_file_name,
    site_name,
    start_date,
    end_date,
    interval,
    pipe_type,
    pipe_size_param,
    depth_column,
    velocity_column,
):
    flow_creator = FDVFlowCreator()

    flow_creator.set_pipe_size(-1.0) 

    if pipe_type == "Circular":
        pipe_size = float(pipe_size_param) / 1000.0
        flow_calculator = CircularCalculator(pipe_size / 2.0)
        if pipe_size > 0.0:
            flow_creator.set_pipe_size(pipe_size)
    elif pipe_type == "Rectangular":
        pipe_size = float(pipe_size_param) / 1000.0
        flow_calculator = RectangularCalculator(pipe_size)
        if pipe_size > 0.0:
            flow_creator.set_pipe_size(pipe_size)
    elif pipe_type == "Egg Type 1":
        egg_params = list(map(float, pipe_size_param.split(",")))
        egg_width, egg_height, egg_r3 = egg_params
        flow_calculator = Egg1Calculator(egg_width, egg_height, egg_r3)
    elif pipe_type == "Egg Type 2a":
        egg_params = list(map(float, pipe_size_param.split(",")))
        egg_width, egg_height, egg_r3 = egg_params
        flow_calculator = Egg2ACalculator(egg_width, egg_height, egg_r3)
    elif pipe_type == "Egg Type 2":
        egg_height = float(pipe_size_param)
        flow_calculator = Egg2Calculator(egg_height)
    elif pipe_type == "Two Circles and a Rectangle":
        circle_rect_params = list(map(float, pipe_size_param.split(",")))
        height, width = circle_rect_params
        flow_calculator = TwoCircleAndRectangleCalculator(width, height)
    else:
        raise ValueError(f"Unsupported pipe type: {pipe_type}")

    flow_creator.set_site_name(site_name)
    flow_creator.set_starting_time(start_date)
    flow_creator.set_ending_time(end_date)
    flow_creator.set_interval(interval)
    flow_creator.set_calculator(flow_calculator)
    flow_creator.set_csv_file(csv_file_name)
    flow_creator.set_output_file(output_file_name)

    flow_creator.write_header()
    flow_creator.write_values(depth_column, velocity_column)
    flow_creator.write_tail()
    flow_creator.close_output_file()

    return flow_creator.get_null_readings()
