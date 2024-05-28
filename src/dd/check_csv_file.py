import os
import pandas as pd
from typing import Optional, Union, Tuple
from src.logger.logger import logger


def calculate_interval(timestamps: pd.Series) -> Optional[pd.Timedelta]:
    """Calculate the most common interval between timestamps."""
    try:
        logger.info("Calculating the most common interval between timestamps.")
        intervals = timestamps.diff().dropna()
        mode_interval = intervals.mode()[0]
        logger.info(f"Most common interval calculated: {mode_interval}")
        return mode_interval
    except Exception as e:
        logger.error(f"Error calculating interval: {e}")
        return None


def fill_gaps(df: pd.DataFrame, interval: pd.Timedelta) -> pd.DataFrame:
    """Fill gaps in the dataframe based on the most common interval."""
    try:
        logger.info("Filling gaps in the dataframe based on the calculated interval.")
        timestamp_column = df.columns[0]
        full_range = pd.date_range(
            start=df[timestamp_column].min(),
            end=df[timestamp_column].max(),
            freq=interval,
        )
        logger.info(
            f"Full date range generated from {df[timestamp_column].min()} to {df[timestamp_column].max()}."
        )
        df.set_index(timestamp_column, inplace=True)
        df = df.reindex(full_range)
        df.index.name = timestamp_column
        df.reset_index(inplace=True)
        logger.info("Gaps filled in the dataframe.")
        return df
    except Exception as e:
        logger.error(f"Error filling gaps: {e}")
        return df


def try_parsing_date(text: str) -> Optional[pd.Timestamp]:
    """Try to parse a date string using multiple formats."""
    date_formats = [
        "%d/%m/%Y %H:%M",
        "%m/%d/%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
    ]
    for fmt in date_formats:
        try:
            return pd.to_datetime(text, format=fmt)
        except ValueError:
            continue
    return pd.NaT


def parse_dates(date_series: pd.Series) -> pd.Series:
    """Parse dates with mixed formats."""
    try:
        logger.info("Parsing dates with mixed formats.")
        parsed_dates = date_series.apply(try_parsing_date)
        logger.info("Dates parsed successfully.")
        return parsed_dates
    except Exception as e:
        logger.error(f"Error parsing dates: {e}")
        return pd.Series([pd.NaT] * len(date_series))


def check_and_fill_csv_file(filepath: str) -> Optional[Tuple[pd.DataFrame, int]]:
    """Check if a CSV file exists and fill any gaps based on the most common interval."""
    try:
        logger.info(f"Checking if file exists: {filepath}")
        if not os.path.exists(filepath):
            logger.error("File does not exist.")
            return None

        # Read the file based on extension
        logger.info(f"Reading the file: {filepath}")
        if filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
            logger.info("File read as CSV.")
        elif filepath.endswith(".xlsx"):
            df = pd.read_excel(filepath)
            logger.info("File read as Excel.")
        else:
            logger.error("Unsupported file format.")
            return None

        # Parse dates in the first column
        logger.info("Parsing dates in the dataframe.")
        df[df.columns[0]] = parse_dates(df[df.columns[0]])
        logger.info("Dates parsed successfully.")

        # Ensure timestamps are sorted
        logger.info("Sorting timestamps in the dataframe.")
        df.sort_values(by=df.columns[0], inplace=True)

        # Calculate interval and fill gaps
        interval = calculate_interval(df[df.columns[0]])
        if interval is not None:
            df = fill_gaps(df, interval)
            gaps_count = df.isnull().sum().sum()  # Count total gaps
            logger.info(f"There are {gaps_count} gaps in the data.")
            df.to_csv(filepath, index=False)
            logger.info(f"CSV file updated and saved to {filepath}")
            return df, gaps_count
        else:
            logger.error("Failed to calculate the interval, cannot fill gaps.")
            return None
    except Exception as e:
        logger.error(f"An error occurred while processing the file: {e}")
        return None
