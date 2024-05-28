from dateutil.parser import parse
from src.calculator.Calculator import Calculator
import pandas as pd


class FDVFlowCreator:
    def __init__(self):
        self.calculator = None
        self.header_lines = [
            "**DATA_FORMAT:           1,ASCII",
            "**IDENTIFIER:            1,SHUTTERT",
            "**FIELD:                 3,FLOW,DEPTH,VELOCITY",
            "**UNITS:                 3,L/S,MM,M/S",
            "**FORMAT:                3,2I5,F5,[5]",
            "**RECORD_LENGTH:         I2,75",
            "**CONSTANTS:             6,HEIGHT,MIN_VEL,MANHOLE_NO,",
            "*+START,END,INTERVAL",
            "**C_UNITS:               6,MM,M/S,,GMT,GMT,MIN",
            "**C_FORMAT:              10,I5,1X,F5,1X,A20/D10,1X,D10,1X,I2",
            "*CSTART",
            "  0.200 UNKNOWN",
        ]
        self.output_file = None
        self.null_readings = 0
        self.value_count = 0
        self.starting_time = None
        self.ending_time = None
        self.interval = None

    def set_pipe_size(self, pipe_size):
        self.header_lines[11] = f"{pipe_size:7.3f} UNKNOWN"

    def set_site_name(self, site_name):
        self.header_lines[1] = "**IDENTIFIER:            1," + (
            site_name.upper() if len(site_name) <= 15 else site_name[:15].upper()
        )

    def set_starting_time(self, starting_time):
        self.starting_time = parse(
            starting_time
            if isinstance(starting_time, str)
            else starting_time.strftime("%Y-%m-%d %H:%M:%S")
        )

    def set_ending_time(self, ending_time):
        self.ending_time = parse(
            ending_time
            if isinstance(ending_time, str)
            else ending_time.strftime("%Y-%m-%d %H:%M:%S")
        )

    def set_interval(self, interval):
        self.interval = interval.total_seconds() / 60

    def set_calculator(self, calculator):
        if not isinstance(calculator, Calculator):
            raise ValueError("calculator must be an instance of a Calculator subclass")
        self.calculator = calculator

    def set_csv_file(self, csv_file):
        self.csv_file = csv_file

    def set_output_file(self, output_file):
        try:
            self.output_file = open(output_file, "w")
        except IOError as e:
            raise IOError(f"Error opening output file {output_file}: {e}")

    def close_output_file(self):
        if self.output_file:
            self.output_file.close()

    def write_header(self):
        for line in self.header_lines:
            self.output_file.write(line + "\n")
        self.output_file.write(f"{self.starting_time.strftime('%Y%m%d%H%M')} ")
        self.output_file.write(f"{self.ending_time.strftime('%Y%m%d%H%M')}   ")
        self.output_file.write(f"{int(self.interval)}\n")
        self.output_file.write("*CEND\n")

    def write_tail(self):
        self.output_file.write("\n*END\n")

    def get_null_readings(self):
        return self.null_readings

    def write_values(self, depth_col=None, velocity_col=None):
        self.value_count = 1
        if not self.output_file:
            raise ValueError("Output file not set.")

        try:
            df = pd.read_csv(self.csv_file)

            if depth_col is None:
                df["depth"] = 0.0
                depth_col = "depth"
            elif depth_col not in df.columns:
                print(f"Depth column '{depth_col}' not found in CSV. Filling with 0.0.")
                df[depth_col] = 0.0

            if velocity_col is None:
                df["velocity"] = 0.0
                velocity_col = "velocity"
            elif velocity_col not in df.columns:
                print(
                    f"Velocity column '{velocity_col}' not found in CSV. Filling with 0.0."
                )
                df[velocity_col] = 0.0

            # Replace missing values with 0.0
            self.null_readings = df[depth_col].isnull().sum()
            df[depth_col] = df[depth_col].fillna(0.0)
            df[velocity_col] = df[velocity_col].fillna(0.0)

            for _, row in df.iterrows():
                depth = float(row[depth_col])
                velocity = float(row[velocity_col])

                result = (
                    0.0
                    if depth == 0.0 or velocity == 0.0
                    else self.calculator.perform_calculation(depth, velocity)
                )
                self._write_output(depth, velocity, result)

            if self.value_count % 5 != 0:
                self.output_file.write("\n")
        except IOError as e:
            print(f"Error reading CSV file {self.csv_file}: {e}")
            raise
        except ValueError as e:
            print(f"Error processing CSV file: {e}")
            raise

    def _write_output(self, depth, velocity, result):
        """Write formatted depth, velocity, and result to the output file."""
        self.output_file.write(
            f"{result:5.0f}{round(depth * 1000.0):5.0f}{velocity:5.2f}"
        )
        if self.value_count % 5 == 0:
            self.output_file.write("\n")
        self.value_count += 1
