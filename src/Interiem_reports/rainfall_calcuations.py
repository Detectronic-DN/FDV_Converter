import os
import pandas as pd


class RainfallTotalsGenerator:
    def __init__(self, backend):
        self.backend = backend
        self.df = self.load_data()

    def load_data(self):
        try:
            df = pd.read_csv(self.backend.final_file_path)
            time_col = self.backend.column_map['timestamp'][0][0]  # Get the first timestamp column name
            df[time_col] = pd.to_datetime(df[time_col])
            df.sort_values(by=time_col, inplace=True)
            df.reset_index(drop=True, inplace=True)
            return df
        except Exception as e:
            self.backend.log_error(f"Error loading data: {e}")
            raise

    def generate_totals(self):
        try:
            time_col = self.backend.column_map['timestamp'][0][0]  # Get the first timestamp column name
            rainfall_cols = self.backend.column_map.get('rainfall', [])

            if not rainfall_cols:
                raise ValueError("No rainfall column found")

            rainfall_col = rainfall_cols[0][0]  # Get the first rainfall column name

            self.backend.log_info(f"Using rainfall column: {rainfall_col}")

            # Daily totals
            daily_totals = self.df.groupby(self.df[time_col].dt.date)[rainfall_col].sum().reset_index()
            daily_totals.columns = ['Date', 'Daily Total (mm)']

            # Weekly totals
            weekly_totals = self.df.groupby(pd.Grouper(key=time_col, freq='W-MON'))[rainfall_col].sum().reset_index()
            weekly_totals.columns = ['Week Starting', 'Weekly Total (mm)']

            return daily_totals, weekly_totals

        except Exception as e:
            self.backend.log_error(f"Error generating rainfall totals: {e}")
            raise

    def save_totals(self, daily_totals, weekly_totals, output_dir):
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            output_file = os.path.join(output_dir, "rainfall_totals.xlsx")
            with pd.ExcelWriter(output_file) as writer:
                daily_totals.to_excel(writer, sheet_name="Daily Totals", index=False)
                weekly_totals.to_excel(writer, sheet_name="Weekly Totals", index=False)

            self.backend.log_info(f"Rainfall totals saved to {output_file}")
        except Exception as e:
            self.backend.log_error(f"Error saving rainfall totals: {e}")
            raise