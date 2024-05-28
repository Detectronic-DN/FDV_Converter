# FDV Converter Application

## Overview

The FDV Converter Application is a comprehensive tool designed to handle and process flow and rainfall data. It allows users to convert CSV data into FDV format, generate interim reports, and calculate specific flow parameters. The application includes a user-friendly interface for easy navigation and operation.

## Features

- **FDV Conversion**: Convert CSV data into FDV format, supporting multiple pipe shapes and sizes.
- **Interim Reports**: Generate weekly and daily summaries of flow data, including total, maximum, and minimum flows.
- **Rainfall Data Conversion**: Convert CSV rainfall data into a specified format.
- **R3 Calculator**: Calculate the R3 value for different egg-shaped pipes.
- **User Authentication**: Save and manage user credentials for secure access.

## Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/Detectronic-DN/FDV_automation.git
    cd fdv-converter
    ```

2. **Set up a virtual environment**:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install the required packages**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Run the application**:
    ```sh
    python src/UI/main.py
    ```

## Usage

### FDV Converter

1. **Login**: Enter your username and password to log in.
2. **Upload CSV File**: Navigate to the file upload section and select a CSV file.
3. **Set Parameters**: Choose the depth column, velocity column, pipe shape, and size.
4. **Create FDV**: Click the "Create FDV" button to generate the FDV file.

### Interim Reports

1. **Generate Reports**: Click the "Interim Reports" button after uploading a CSV file.
2. **View Reports**: The reports will be saved in the specified directory, with separate files for each interim period.

### Rainfall Conversion

1. **Select Rainfall Column**: Choose the appropriate column for rainfall data.
2. **Create Rainfall File**: Click the "Create Rainfall" button to generate the file.

### R3 Calculator

1. **Enter Dimensions**: Provide the pipe width and height.
2. **Calculate R3**: Click the "Calculate R3" button to get the R3 value.
3. **Use in FDV**: You can use the calculated R3 value directly in the FDV converter.

