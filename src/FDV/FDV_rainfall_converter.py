from src.FDV.FDV_rainfall_creator import FDVRainfallCreator


def perform_r_conversion(
    csv_file_name, output_file_name, site_name, start_date, end_date, interval, rainfall_column
):
    rainfall_creator = FDVRainfallCreator()
    rainfall_creator.set_site_name(site_name)
    rainfall_creator.set_starting_time(start_date)
    rainfall_creator.set_ending_time(end_date)
    rainfall_creator.set_interval(interval)
    rainfall_creator.set_csv_file(csv_file_name)
    rainfall_creator.set_output_file(output_file_name)
    rainfall_creator.write_header()
    rainfall_creator.write_values(rainfall_column)
    rainfall_creator.write_tail()
    rainfall_creator.close_output_file()
    return rainfall_creator.get_null_readings()
