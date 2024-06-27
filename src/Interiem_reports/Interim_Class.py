import os
from datetime import timedelta
from typing import Tuple, Optional

import pandas as pd


class InterimReportGenerator:
    def __init__(self, backend):
        self.backend = backend
        self.df = self.load_data()
        self.monitor_type = self.backend.monitor_type
        self.columns = self.backend.column_map
        self.interval = pd.to_timedelta(self.backend.interval)
        self.interval_seconds = int(self.interval.total_seconds())

    def load_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.backend.final_file_path)
        time_column = self.backend.column_map['timestamp'][0]
        df[time_column] = pd.to_datetime(df[time_column])
        df.sort_values(by=time_column, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def calculate_values(self) -> pd.DataFrame:
        if self.monitor_type == "Flow":
            flow_column = self.columns['flow'][0]
            self.df["L"] = self.df[flow_column] * self.interval_seconds
            self.df["m3"] = self.df["L"] / 1000
        elif self.monitor_type == "Depth":
            # For depth, we don't need additional calculations
            pass
        elif self.monitor_type == "Rainfall":
            # For rainfall, we might want to calculate cumulative rainfall
            rainfall_column = self.columns['rainfall'][0]
            self.df["Cumulative_Rainfall"] = self.df[rainfall_column].cumsum()
        return self.df

    def generate_summaries(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        time_column = self.columns['timestamp'][0]

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
            week_end = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
            weekly_data = self.df[(self.df[time_column] >= start_date) & (self.df[time_column] <= week_end)]

            if not weekly_data.empty:
                summary = {"Start Date": start_date, "End Date": week_end, }
                if self.monitor_type == "Flow":
                    flow_column = self.columns['flow'][0]
                    summary.update(
                        {"Total Flow(m3)": weekly_data["m3"].sum(), "Max Flow(l/s)": weekly_data[flow_column].max(),
                         "Min Flow(l/s)": weekly_data[flow_column].min(), })
                elif self.monitor_type == "Depth":
                    depth_column = self.columns['depth'][0]
                    summary.update({"Average Level(m)": weekly_data[depth_column].mean(),
                                    "Max Level(m)": weekly_data[depth_column].max(),
                                    "Min Level(m)": weekly_data[depth_column].min(), })
                weekly_summaries.append(summary)
            start_date = week_end + timedelta(seconds=1)

        summary_df = pd.DataFrame(weekly_summaries)
        summary_df["Start Date"] = summary_df["Start Date"].dt.strftime("%d/%m/%Y")
        summary_df["End Date"] = summary_df["End Date"].dt.strftime("%d/%m/%Y")
        summary_df["Date Range"] = summary_df["Start Date"] + " - " + summary_df["End Date"]
        summary_df["Interim Period"] = summary_df.index.map(lambda x: f"Interim {x + 1}")

        columns = ["Interim Period", "Date Range"]
        if self.monitor_type == "Flow":
            columns.extend(["Total Flow(m3)", "Max Flow(l/s)", "Min Flow(l/s)"])
        elif self.monitor_type == "Depth":
            columns.extend(["Average Level(m)", "Max Level(m)", "Min Level(m)"])

        summary_df = summary_df[columns]
        return summary_df

    def calculate_daily_summary(self) -> pd.DataFrame:
        time_column = self.columns['timestamp'][0]

        if self.monitor_type == "Flow":
            flow_column = self.columns['flow'][0]
            daily_summary = (self.df.groupby(pd.Grouper(key=time_column, freq="D")).agg(
                {flow_column: ["sum", "max", "min"], "m3": "sum"}).reset_index())
            daily_summary.columns = ["Date", "Total Flow(l/s)", "Max Flow(l/s)", "Min Flow(l/s)", "Flow (m3)", ]
        elif self.monitor_type == "Depth":
            depth_column = self.columns['depth'][0]
            daily_summary = (self.df.groupby(pd.Grouper(key=time_column, freq="D")).agg(
                {depth_column: ["mean", "max", "min"]}).reset_index())
            daily_summary.columns = ["Date", "Average Level(m)", "Max Level(m)", "Min Level(m)", ]

        daily_summary["Date"] = daily_summary["Date"].dt.strftime("%d/%m/%Y")
        return daily_summary

    @staticmethod
    def save_interim_files(report_df: pd.DataFrame, daily_summary: pd.DataFrame, output_dir: str) -> None:
        for index, row in report_df.iterrows():
            if row["Interim Period"] == "Grand Total":
                continue
            date_range = row["Date Range"]
            start_date, end_date = date_range.split(" - ")
            start_date = pd.to_datetime(start_date, format="%d/%m/%Y")
            end_date = pd.to_datetime(end_date, format="%d/%m/%Y")

            filtered_daily_summary = daily_summary[
                (pd.to_datetime(daily_summary["Date"], format="%d/%m/%Y") >= start_date) & (
                        pd.to_datetime(daily_summary["Date"], format="%d/%m/%Y") <= end_date)]

            interim_dir = os.path.join(output_dir, row["Interim Period"])
            if not os.path.exists(interim_dir):
                os.makedirs(interim_dir)
            output_file = os.path.join(interim_dir, f"{row['Interim Period']}.xlsx")
            filtered_daily_summary.to_excel(output_file, index=False)

    def generate_report(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        self.calculate_values()
        summaries_df = self.generate_summaries()
        daily_summary = self.calculate_daily_summary()

        # Add Grand Total row
        grand_total_row = {"Interim Period": "Grand Total", "Date Range": ""}
        if self.monitor_type == "Flow":
            grand_total_row.update({"Total Flow(m3)": summaries_df["Total Flow(m3)"].sum(),
                                    "Max Flow(l/s)": summaries_df["Max Flow(l/s)"].max(),
                                    "Min Flow(l/s)": summaries_df["Min Flow(l/s)"].min(), })
        elif self.monitor_type == "Depth":
            grand_total_row.update({"Average Level(m)": summaries_df["Average Level(m)"].mean(),
                                    "Max Level(m)": summaries_df["Max Level(m)"].max(),
                                    "Min Level(m)": summaries_df["Min Level(m)"].min(), })
        elif self.monitor_type == "Rainfall":
            grand_total_row.update({"Total Rainfall": summaries_df["Total Rainfall"].sum(),
                                    "Max Rainfall": summaries_df["Max Rainfall"].max(),
                                    "Min Rainfall": summaries_df["Min Rainfall"].min(), })

        summaries_df = pd.concat([summaries_df, pd.DataFrame([grand_total_row])], ignore_index=True)

        return summaries_df, self.df, daily_summary
