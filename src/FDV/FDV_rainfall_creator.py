from dateutil.parser import parse
import pandas as pd


class FDVRainfallCreator:
    def __init__(self) -> None:
        self.header_lines = [
            "**DATA_FORMAT:           1,ASCII",
            "**IDENTIFIER:            1,SHUTTE",
            "**FIELD:                 1,INTENSITY",
            "**UNITS:                 1,MM/HR",
            "**FORMAT:                2,F15.1,[5]",
            "**RECORD_LENGTH:         I2,75",
            "**CONSTANTS:             35,LOCATION,0_ANT_RAIN,1_ANT_RAIN,2_ANT_RAIN,",
            "*+                       3_ANT_RAIN,4_ANT_RAIN,5_ANT_RAIN,6_ANT_RAIN,",
            "*+                       7_ANT_RAIN,8_ANT_RAIN,9_ANT_RAIN,10_ANT_RAIN,",
            "*+                       11_ANT_RAIN,12_ANT_RAIN,13_ANT_RAIN,14_ANT_RAIN,",
            "*+                       15_ANT_RAIN,16_ANT_RAIN,17_ANT_RAIN,18_ANT_RAIN,",
            "*+                       19_ANT_RAIN,20_ANT_RAIN,21_ANT_RAIN,22_ANT_RAIN,",
            "*+                       23_ANT_RAIN,24_ANT_RAIN,25_ANT_RAIN,26_ANT_RAIN,",
            "*+                       27_ANT_RAIN,28_ANT_RAIN,29_ANT_RAIN,30_ANT_RAIN,",
            "*+                       START,END,INTERVAL",
            "**C_UNITS:               35, ,MM,MM,MM,MM,MM,MM,MM,MM,MM,MM,",
            "**C_UNITS:               MM,MM,MM,MM,MM,MM,MM,MM,MM,MM,MM,",
            "**C_UNITS:               MM,MM,MM,MM,MM,MM,MM,MM,MM,MM,GMT,GMT,MIN",
            "**C_FORMAT:              8,A20,F7.2/15F5.1/15F5.1/D10,2X,D10,I4",
            "*CSTART",
            "UNKNOWN              -1.0 ",
            "-1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 ",
            "-1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 ",
        ]
        self.drain_size = 10
        self.output_buffer = []
        self.null_readings = 0
        self.value_count = 0
        self.starting_time = None
        self.ending_time = None
        self.interval = 120

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

    def set_csv_file(self, csv_file):
        self.csv_file = csv_file

    def set_output_file(self, output_file):
        try:
            self.output_file = open(output_file, "w")
        except IOError as e:
            print(f"Error opening output file {output_file}: {e}")
            raise

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
        if (self.value_count - 1) % 5 != 0:
            self.output_file.write("\n")
        self.output_file.write("\n*END\n")

    def get_null_readings(self):
        return self.null_readings

    def insert_values(self, samp):
        sample = float(samp)
        if sample > 1.0e-5:
            count = 0
            offs = len(self.output_buffer) - 1
            divisor = 1.0
            while offs >= 0 and count < 4:
                sa = self.output_buffer[offs]
                if sa >= 1.0e-5:
                    break
                divisor += 1
                count += 1
                offs -= 1
            offs += 1
            if count > 0 and sample > 6.0:
                sample = 6.0 / (divisor - 1.0)
                while offs < len(self.output_buffer):
                    self.output_buffer[offs] = sample
                    offs += 1
                sample = float(samp) - 6.0
            else:
                sample /= divisor
                while offs < len(self.output_buffer):
                    self.output_buffer[offs] = sample
                    offs += 1

        self.output_buffer.append(sample)
        if len(self.output_buffer) >= 10:
            self.drain_output_buffer(self.drain_size)

    def drain_output_buffer(self, drainSize):
        while len(self.output_buffer) > drainSize:
            sample = self.output_buffer.pop(0)
            self.output_file.write(f"{sample:15.1f}")
            if self.value_count % 5 == 0:
                self.output_file.write("\n")
            self.value_count += 1

    def write_values(self, rain_col=None):
        self.value_count = 1
        if not self.output_file:
            raise ValueError("Output file not set.")

        try:
            df = pd.read_csv(self.csv_file)

            if rain_col is None:
                raise ValueError("Rainfall column not specified.")

            if rain_col not in df.columns:
                df[rain_col] = 0.0
            else:
                df[rain_col] = df[rain_col].fillna(0.0)

            for _, row in df.iterrows():
                rainfall = 0.0 if pd.isna(row[rain_col]) else row[rain_col]
                self.insert_values(rainfall)

            self.drain_output_buffer(0)

        except IOError as e:
            print(f"Error reading CSV file {self.csv_file}: {e}")
            raise
