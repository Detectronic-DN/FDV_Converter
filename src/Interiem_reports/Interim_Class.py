import os
from datetime import timedelta
from typing import Tuple, Optional

import pandas as pd


class InterimReportGenerator:
    def __init__(self, backend):
        """
        Initializes the InterimReportGenerator with the provided backend.
        """
        self.backend = backend
        self.columns = self.backend.column_map
        self.monitor_type = self.backend.monitor_type
        self.df = self.load_data()
        self.interval = pd.to_timedelta(self.backend.interval)
        self.interval_seconds = int(self.interval.total_seconds())

    def load_data(self) -> pd.DataFrame:
        """
        Loads and processes the data from the backend's final file path.

        Returns:
            pd.DataFrame: The processed DataFrame.
        """
        try:
            df = pd.read_csv(self.backend.final_file_path)
            self.backend.log_info(f"Data loaded from {self.backend.final_file_path}")
            time_column = (
                self.columns["timestamp"][0][0] if self.columns["timestamp"] else None
            )
            if not time_column:
                raise ValueError("Timestamp column not found")
            df[time_column] = pd.to_datetime(df[time_column])
            df.sort_values(by=time_column, inplace=True)
            df.reset_index(drop=True, inplace=True)
            return df
        except Exception as e:
            self.backend.log_error(f"Error loading data: {e}")
            raise

    def calculate_values(self) -> pd.DataFrame:
        """
        Calculates additional values for the DataFrame based on the monitor type.

        Returns:
            pd.DataFrame: The DataFrame with calculated values.
        """
        try:
            if self.monitor_type == "Flow":
                flow_column = (
                    self.columns["flow"][0][0] if self.columns["flow"] else None
                )
                if flow_column:
                    self.df["L"] = self.df[flow_column] * self.interval_seconds
                    self.df["m3"] = self.df["L"] / 1000
            elif self.monitor_type == "Depth":
                # Add depth specific calculations if needed
                pass
            elif self.monitor_type == "Rainfall":
                # Add rainfall specific calculations if needed
                pass
            return self.df
        except KeyError as e:
            self.backend.log_error(f"KeyError in calculate_values: {e}")
            raise
        except Exception as e:
            self.backend.log_error(f"Error in calculate_values: {e}")
            raise

    def generate_summaries(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Generates weekly summaries for the data.

        Args:
            start_date (Optional[str]): The start date for the summaries.
            end_date (Optional[str]): The end date for the summaries.

        Returns:
            pd.DataFrame: The DataFrame containing weekly summaries.
        """
        try:
            time_column = (
                self.columns["timestamp"][0][0] if self.columns["timestamp"] else None
            )
            if not time_column:
                raise ValueError("Timestamp column not found")

            if start_date is None:
                start_date = self.df[time_column].min().normalize()
            else:
                start_date = pd.to_datetime(start_date).normalize()

            if end_date is None:
                end_date = self.df[time_column].max().normalize()
            else:
                end_date = pd.to_datetime(end_date).normalize()
            end_date += timedelta(days=1) - timedelta(seconds=1)

            weekly_summaries = []
            while start_date <= end_date:
                week_end = start_date + timedelta(
                    days=6, hours=23, minutes=59, seconds=59
                )
                weekly_data = self.df[
                    (self.df[time_column] >= start_date)
                    & (self.df[time_column] <= week_end)
                ]

                if not weekly_data.empty:
                    summary = {
                        "Start Date": start_date,
                        "End Date": week_end,
                    }
                    if self.monitor_type == "Flow":
                        flow_column = (
                            self.columns["flow"][0][0] if self.columns["flow"] else None
                        )
                        if flow_column:
                            summary.update(
                                {
                                    "Total Flow(m3)": weekly_data["m3"].sum(),
                                    "Max Flow(l/s)": weekly_data[flow_column].max(),
                                    "Min Flow(l/s)": weekly_data[flow_column].min(),
                                }
                            )
                    elif self.monitor_type == "Depth":
                        depth_column = (
                            self.columns["depth"][0][0]
                            if self.columns["depth"]
                            else None
                        )
                        if depth_column:
                            summary.update(
                                {
                                    "Average Level(m)": weekly_data[
                                        depth_column
                                    ].mean(),
                                    "Max Level(m)": weekly_data[depth_column].max(),
                                    "Min Level(m)": weekly_data[depth_column].min(),
                                }
                            )
                    weekly_summaries.append(summary)
                start_date = week_end + timedelta(seconds=1)

            summary_df = pd.DataFrame(weekly_summaries)
            summary_df["Start Date"] = summary_df["Start Date"].dt.strftime("%d/%m/%Y")
            summary_df["End Date"] = summary_df["End Date"].dt.strftime("%d/%m/%Y")
            summary_df["Date Range"] = (
                summary_df["Start Date"] + " - " + summary_df["End Date"]
            )
            summary_df["Interim Period"] = summary_df.index.map(
                lambda x: f"Interim {x + 1}"
            )

            columns = ["Interim Period", "Date Range"]
            if self.monitor_type == "Flow":
                columns.extend(["Total Flow(m3)", "Max Flow(l/s)", "Min Flow(l/s)"])
            elif self.monitor_type == "Depth":
                columns.extend(["Average Level(m)", "Max Level(m)", "Min Level(m)"])

            summary_df = summary_df[columns]
            return summary_df
        except Exception as e:
            self.backend.log_error(f"Error generating summaries: {e}")
            raise

    def calculate_daily_summary(self) -> pd.DataFrame:
        """
        Calculates daily summaries for the data.

        Returns:
            pd.DataFrame: The DataFrame containing daily summaries.
        """
        try:
            time_column = (
                self.columns["timestamp"][0][0] if self.columns["timestamp"] else None
            )
            if not time_column:
                raise ValueError("Timestamp column not found")

            if self.monitor_type == "Flow":
                flow_column = (
                    self.columns["flow"][0][0] if self.columns["flow"] else None
                )
                if flow_column:
                    daily_summary = (
                        self.df.groupby(pd.Grouper(key=time_column, freq="D"))
                        .agg({flow_column: ["mean", "max", "min"], "m3": "sum"})
                        .reset_index()
                    )
                    daily_summary.columns = [
                        "Date",
                        "Average Flow(l/s)",
                        "Max Flow(l/s)",
                        "Min Flow(l/s)",
                        "Flow (m3)",
                    ]
            elif self.monitor_type == "Depth":
                depth_column = (
                    self.columns["depth"][0][0] if self.columns["depth"] else None
                )
                if depth_column:
                    daily_summary = (
                        self.df.groupby(pd.Grouper(key=time_column, freq="D"))
                        .agg({depth_column: ["mean", "max", "min"]})
                        .reset_index()
                    )
                    daily_summary.columns = [
                        "Date",
                        "Average Level(m)",
                        "Max Level(m)",
                        "Min Level(m)",
                    ]

            daily_summary["Date"] = daily_summary["Date"].dt.strftime("%d/%m/%Y")
            return daily_summary
        except KeyError as e:
            self.backend.log_error(f"KeyError in calculate_daily_summary: {e}")
            raise
        except Exception as e:
            self.backend.log_error(f"Error in calculate_daily_summary: {e}")
            raise

    def generate_report(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Generates the interim report, including summaries and daily summaries.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: The summary DataFrame, the original DataFrame,
            and the daily summary DataFrame.
        """
        try:
            self.calculate_values()
            summaries_df = self.generate_summaries()
            daily_summary = self.calculate_daily_summary()

            # Add Grand Total row
            grand_total_row = {"Interim Period": "Grand Total", "Date Range": ""}
            if self.monitor_type == "Flow":
                grand_total_row.update(
                    {
                        "Total Flow(m3)": summaries_df["Total Flow(m3)"].sum(),
                        "Max Flow(l/s)": summaries_df["Max Flow(l/s)"].max(),
                        "Min Flow(l/s)": summaries_df["Min Flow(l/s)"].min(),
                    }
                )
            elif self.monitor_type == "Depth":
                grand_total_row.update(
                    {
                        "Average Level(m)": summaries_df["Average Level(m)"].mean(),
                        "Max Level(m)": summaries_df["Max Level(m)"].max(),
                        "Min Level(m)": summaries_df["Min Level(m)"].min(),
                    }
                )
            elif self.monitor_type == "Rainfall":
                grand_total_row.update(
                    {
                        "Total Rainfall": summaries_df["Total Rainfall"].sum(),
                        "Max Rainfall": summaries_df["Max Rainfall"].max(),
                        "Min Rainfall": summaries_df["Min Rainfall"].min(),
                    }
                )

            summaries_df = pd.concat(
                [summaries_df, pd.DataFrame([grand_total_row])], ignore_index=True
            )

            return summaries_df, self.df, daily_summary
        except Exception as e:
            self.backend.log_error(f"Error generating report: {e}")
            raise

    def save_final_report(
        self,
        summaries_df: pd.DataFrame,
        values_df: pd.DataFrame,
        daily_summary: pd.DataFrame,
        output_dir: str,
    ) -> None:
        """
        Saves the final report to a single Excel file with three sheets: Values, Summary, and Daily.

        Args:
            summaries_df (pd.DataFrame): The DataFrame containing the summary data.
            values_df (pd.DataFrame): The original DataFrame containing the values' data.
            daily_summary (pd.DataFrame): The DataFrame containing the daily summary data.
            output_dir (str): The directory to save the final report.
        """
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            output_file = os.path.join(
                output_dir,
                f"{os.path.basename(self.backend.final_file_path).split('.')[0]}_final_report"
                f".xlsx",
            )
            with pd.ExcelWriter(output_file) as writer:
                values_df.to_excel(writer, sheet_name="Values", index=False)
                summaries_df.to_excel(writer, sheet_name="Summary", index=False)
                daily_summary.to_excel(writer, sheet_name="Daily", index=False)

            self.backend.log_info(f"Final report saved to {output_file}")
        except Exception as e:
            self.backend.log_error(f"Error saving final report: {e}")
            raise
