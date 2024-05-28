from src.FDV.FDV_rainfall_creator import FDVRainfallCreator


def perform_R_conversion(
    csvFileName, outputFileName, siteName, startDate, endDate, interval, rainfall_column
):
    rainfallCreator = FDVRainfallCreator()
    rainfallCreator.set_site_name(siteName)
    rainfallCreator.set_starting_time(startDate)
    rainfallCreator.set_ending_time(endDate)
    rainfallCreator.set_interval(interval)
    rainfallCreator.set_csv_file(csvFileName)
    rainfallCreator.set_output_file(outputFileName)
    rainfallCreator.write_header()
    rainfallCreator.write_values(rainfall_column)
    rainfallCreator.write_tail()
    rainfallCreator.close_output_file()
    return rainfallCreator.get_null_readings()
