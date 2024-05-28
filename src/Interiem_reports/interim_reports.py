import os
import pandas as pd
from datetime import timedelta
from src.dd.check_csv_file import calculate_interval

def calculate_flow_values(df, flow_col, interval):
    """
    Calculate flow values based on the given dataframe, flow column, and interval rate.
    """
    try:
        df["L"] = df[flow_col] * interval
        df["m3"] = df["L"] / 1000
        return df
    except KeyError:
        print(f"Column {flow_col} not found in the dataframe.")
        return df

def generate_summaries(df, flow_column, time_column, start_date=None, end_date=None):
    """
    Generate summaries for the given dataframe based on the given flow column, time column, and interval rate.
    """
    df[time_column] = pd.to_datetime(df[time_column])
    if start_date is None:
        start_date = df[time_column].min().normalize()  # Set time to 00:00:00
    else:
        start_date = pd.to_datetime(start_date).normalize()  # Ensure time is set to 00:00:00

    if end_date is None:
        end_date = df[time_column].max().normalize()
    else:
        end_date = pd.to_datetime(end_date).normalize()
    end_date = end_date + timedelta(days=1) - timedelta(seconds=1)  # To make it till 23:59:59

    weekly_summaries = []
    while start_date <= end_date:
        week_end = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        weekly_data = df[(df[time_column] >= start_date) & (df[time_column] <= week_end)]
        if not weekly_data.empty:
            weekly_summary = {
                "Start Date": start_date,
                "End Date": week_end,
                "Sum of m3": weekly_data["m3"].sum(),
                "Max of l/s": weekly_data[flow_column].max(),
                "Min of l/s": weekly_data[flow_column].min(),
            }
            weekly_summaries.append(weekly_summary)
        start_date = week_end + timedelta(seconds=1)

    summary_df = pd.DataFrame(weekly_summaries)
    summary_df["Start Date"] = summary_df["Start Date"].dt.strftime("%d/%m/%Y")
    summary_df["End Date"] = summary_df["End Date"].dt.strftime("%d/%m/%Y")
    summary_df["Date Range"] = summary_df["Start Date"] + " - " + summary_df["End Date"]
    summary_df["Interim Period"] = summary_df.index.map(lambda x: f"Interim {x + 1}")
    summary_df = summary_df.rename(columns={
        "Sum of m3": "Total Flow(m3)",
        "Max of l/s": "Max Flow(l/s)",
        "Min of l/s": "Min Flow(l/s)",
    })
    summary_df = summary_df[[
        "Interim Period",
        "Date Range",
        "Total Flow(m3)",
        "Max Flow(l/s)",
        "Min Flow(l/s)",
    ]]
    return summary_df

def create_interim_report(df, flow_column, time_column, interval):
    """
    Create an interim report for the given dataframe based on the given flow column, time column, and interval rate.
    """
    values_df = calculate_flow_values(df, flow_column, interval)
    summaries_df = generate_summaries(values_df, flow_column, time_column)

    grand_total_row = {
        "Interim Period": "Grand Total",
        "Date Range": "",
        "Total Flow(m3)": summaries_df["Total Flow(m3)"].sum(),
        "Max Flow(l/s)": summaries_df["Max Flow(l/s)"].max(),
        "Min Flow(l/s)": summaries_df["Min Flow(l/s)"].min(),
    }
    summaries_df = pd.concat([summaries_df, pd.DataFrame([grand_total_row])], ignore_index=True)
    return summaries_df, values_df

def calculate_daily_summary(df, time_column, flow_column):
    """
    Calculate daily summary statistics for the flow column.
    """
    daily_summary = (
        df.groupby(pd.Grouper(key=time_column, freq="D"))
        .agg({flow_column: ["sum", "max", "min"]})
        .reset_index()
    )

    # Rename columns
    daily_summary.columns = ["Date", "Total Flow(l/s)", "Max Flow(l/s)", "Min Flow(l/s)"]
    daily_summary["Total Flow(l/s)"] = daily_summary["Total Flow(l/s)"] * 120
    daily_summary["Flow (m3)"] = daily_summary["Total Flow(l/s)"] / 1000
    daily_summary["Date"] = daily_summary["Date"].dt.strftime('%d/%m/%Y')
    return daily_summary

def save_interim_files(report_df, daily_summary, output_dir):
    """
    Save separate files for each interim period.
    """
    for index, row in report_df.iterrows():
        if row["Interim Period"] == "Grand Total":
            continue
        date_range = row["Date Range"]
        start_date, end_date = date_range.split(" - ")
        start_date = pd.to_datetime(start_date, format="%d/%m/%Y")
        end_date = pd.to_datetime(end_date, format="%d/%m/%Y")

        filtered_daily_summary = daily_summary[
            (pd.to_datetime(daily_summary["Date"], format="%d/%m/%Y") >= start_date) &
            (pd.to_datetime(daily_summary["Date"], format="%d/%m/%Y") <= end_date)
        ]

        interim_dir = os.path.join(output_dir, row["Interim Period"])
        if not os.path.exists(interim_dir):
            os.makedirs(interim_dir)

        output_file = os.path.join(interim_dir, f"{row['Interim Period']}.xlsx")
        filtered_daily_summary.to_excel(output_file, index=False)
