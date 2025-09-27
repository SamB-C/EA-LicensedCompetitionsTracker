import pandas as pd
from pathlib import Path
from datetime import datetime
import requests
import time


def get_latest_spreadsheet(downloads_folder="downloads"):
    """
    Get the most recently downloaded spreadsheet from the downloads folder.

    Args:
        downloads_folder (str): Path to the downloads folder (relative to script directory)

    Returns:
        str: Path to the latest spreadsheet file, or None if no files found
    """
    # Get the absolute path to the script directory
    script_dir = Path(__file__).parent.absolute()
    downloads_path = script_dir / downloads_folder

    if not downloads_path.exists():
        print(f"Downloads folder '{downloads_folder}' does not exist.")
        return None

    # Look for Excel and CSV files
    file_patterns = ['*.xlsx', '*.xls', '*.csv']
    all_files = []

    for pattern in file_patterns:
        files = list(downloads_path.glob(pattern))
        all_files.extend(files)

    if not all_files:
        print(f"No spreadsheet files found in '{downloads_folder}' folder.")
        return None

    # Sort by modification time (most recent first)
    latest_file = max(all_files, key=lambda f: f.stat().st_mtime)

    return str(latest_file)


def list_available_spreadsheets(downloads_folder="downloads"):
    """
    List all available spreadsheet files in the downloads folder.

    Args:
        downloads_folder (str): Path to the downloads folder (relative to script directory)

    Returns:
        list: List of file paths
    """
    # Get the absolute path to the script directory
    script_dir = Path(__file__).parent.absolute()
    downloads_path = script_dir / downloads_folder

    if not downloads_path.exists():
        return []

    file_patterns = ['*.xlsx', '*.xls', '*.csv']
    all_files = []

    for pattern in file_patterns:
        files = list(downloads_path.glob(pattern))
        all_files.extend(files)

    # Sort by modification time (most recent first)
    all_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    return [str(f) for f in all_files]


def parse_spreadsheet_to_dataframe(file_path, sheet_name=None):
    """
    Convert a spreadsheet file to a pandas DataFrame.

    Args:
        file_path (str): Path to the spreadsheet file
        sheet_name (str, optional): Name of the sheet to read (for Excel files)

    Returns:
        pd.DataFrame: The parsed data as a DataFrame
    """
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"Parsing spreadsheet: {file_path.name}")
        print(f"File size: {file_path.stat().st_size:,} bytes")

        # Determine file type and read accordingly
        file_extension = file_path.suffix.lower()

        if file_extension == '.csv':
            # Try different encodings for CSV files
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"Successfully read CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                raise ValueError(
                    "Could not read CSV file with any supported encoding")

        elif file_extension in ['.xlsx', '.xls']:
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"Read sheet: {sheet_name}")
            else:
                # Read the first sheet by default
                df = pd.read_excel(file_path)
                print("Read first sheet (default)")

        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        print(f"DataFrame shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
        print(f"Columns: {list(df.columns)}")

        return df

    except Exception as e:
        print(f"Error parsing spreadsheet: {e}")
        return None


def enrich_with_coordinates(df, postcode_column=None):
    """
    Enrich dataframe with longitude and latitude columns for postcodes.

    Args:
        df (pd.DataFrame): DataFrame containing postcode data
        postcode_column (str): Name of the postcode column (auto-detected if None)

    Returns:
        pd.DataFrame: DataFrame with added longitude and latitude columns
    """
    if df is None or df.empty:
        return df

    # Auto-detect postcode column if not specified
    if postcode_column is None:
        postcode_cols = [col for col in df.columns if 'postcode' in col.lower(
        ) or 'post code' in col.lower()]
        if not postcode_cols:
            print("No postcode column found - skipping coordinate enrichment")
            return df
        postcode_column = postcode_cols[0]

    print(f"Enriching coordinates for column: {postcode_column}")

    # Get unique postcodes to minimize API calls
    unique_postcodes = df[postcode_column].dropna().unique()
    print(f"Found {len(unique_postcodes)} unique postcodes to lookup")

    # Create coordinate lookup dictionary
    coord_cache = {}
    failed_lookups = 0

    for i, postcode in enumerate(unique_postcodes, 1):
        if pd.isna(postcode) or str(postcode).strip() == '':
            continue

        formatted_postcode = str(postcode).strip().upper()

        try:
            # Call postcodes.io API
            response = requests.get(
                f"https://api.postcodes.io/postcodes/{formatted_postcode}")

            if response.status_code == 200:
                data = response.json()
                if data['status'] == 200:
                    coord_cache[postcode] = {
                        'longitude': data['result']['longitude'],
                        'latitude': data['result']['latitude']
                    }
                else:
                    coord_cache[postcode] = {
                        'longitude': None, 'latitude': None}
                    failed_lookups += 1
            else:
                coord_cache[postcode] = {'longitude': None, 'latitude': None}
                failed_lookups += 1

        except Exception as e:
            print(f"Error looking up postcode {formatted_postcode}: {e}")
            coord_cache[postcode] = {'longitude': None, 'latitude': None}
            failed_lookups += 1

        # Show progress and rate limit
        if i % 10 == 0 or i == len(unique_postcodes):
            print(
                f"  Progress: {i}/{len(unique_postcodes)} postcodes processed")

        # Rate limiting - be respectful to the free API
        time.sleep(0.1)

    # Add coordinate columns to dataframe
    df['longitude'] = df[postcode_column].map(
        lambda pc: coord_cache.get(pc, {}).get('longitude'))
    df['latitude'] = df[postcode_column].map(
        lambda pc: coord_cache.get(pc, {}).get('latitude'))

    successful_lookups = len(unique_postcodes) - failed_lookups
    print(
        f"Coordinate enrichment complete: {successful_lookups}/{len(unique_postcodes)} successful lookups")

    return df


def explore_excel_sheets(file_path):
    """
    Explore all sheets in an Excel file.

    Args:
        file_path (str): Path to the Excel file

    Returns:
        dict: Dictionary with sheet names as keys and basic info as values
    """
    try:
        file_path = Path(file_path)

        if file_path.suffix.lower() not in ['.xlsx', '.xls']:
            print("This function only works with Excel files.")
            return {}

        # Get all sheet names
        excel_file = pd.ExcelFile(file_path)
        sheet_info = {}

        print(f"Excel file: {file_path.name}")
        print(f"Available sheets: {len(excel_file.sheet_names)}")
        print("-" * 50)

        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheet_info[sheet_name] = {
                    'rows': df.shape[0],
                    'columns': df.shape[1],
                    'column_names': list(df.columns)
                }

                print(f"Sheet: {sheet_name}")
                print(f"  Size: {df.shape[0]:,} rows × {df.shape[1]} columns")
                print(
                    f"  Columns: {list(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
                print()

            except Exception as e:
                print(f"Error reading sheet '{sheet_name}': {e}")
                sheet_info[sheet_name] = {'error': str(e)}

        return sheet_info

    except Exception as e:
        print(f"Error exploring Excel file: {e}")
        return {}


def display_dataframe_summary(df):
    """
    Display a summary of the DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to summarize
    """
    if df is None or df.empty:
        print("DataFrame is empty or None")
        return

    print("DataFrame Summary:")
    print("=" * 50)
    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print()

    print("Column Information:")
    print(df.info())
    print()

    print("First 5 rows:")
    print(df.head())
    print()

    print("Data types:")
    print(df.dtypes)
    print()

    # Check for missing values
    missing_values = df.isnull().sum()
    if missing_values.any():
        print("Missing values:")
        print(missing_values[missing_values > 0])
    else:
        print("No missing values found")


def main():
    """Main function to demonstrate the spreadsheet parsing functionality."""
    print("Licensed Competitions Tracker - Spreadsheet Parser")
    print("=" * 60)

    # Get the absolute path to the script directory
    script_dir = Path(__file__).parent.absolute()
    print(f"Script directory: {script_dir}")
    print()

    # List available spreadsheets
    available_files = list_available_spreadsheets()

    if not available_files:
        print("No spreadsheet files found in the downloads folder.")
        print("Please run DownloadSpreadsheet.py first to download a spreadsheet.")
        return

    print(f"Found {len(available_files)} spreadsheet file(s):")
    for i, file_path in enumerate(available_files, 1):
        file_name = Path(file_path).name
        file_size = Path(file_path).stat().st_size
        mod_time = datetime.fromtimestamp(Path(file_path).stat().st_mtime)
        print(
            f"  {i}. {file_name} ({file_size:,} bytes, modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')})")

    print()

    # Get the latest spreadsheet
    latest_file = get_latest_spreadsheet()
    print(f"Using latest file: {Path(latest_file).name}")
    print()

    # If it's an Excel file, explore sheets first
    if Path(latest_file).suffix.lower() in ['.xlsx', '.xls']:
        print("Exploring Excel sheets...")
        sheet_info = explore_excel_sheets(latest_file)
        print()

    # Parse the spreadsheet to DataFrame
    df = parse_spreadsheet_to_dataframe(latest_file)

    if df is not None:
        print()
        display_dataframe_summary(df)

        # Enrich with coordinates
        print("\n" + "=" * 60)
        print("ENRICHING WITH COORDINATES")
        print("=" * 60)
        df_enriched = enrich_with_coordinates(df)

        # Save a sample of the enriched data as CSV for inspection (using absolute path)
        script_dir = Path(__file__).parent.absolute()
        sample_file = script_dir / "parsed_data_sample.csv"
        sample_df = df_enriched.head(10) if len(
            df_enriched) > 10 else df_enriched
        sample_df.to_csv(sample_file, index=False)
        print(f"\nSaved enriched sample data to: {sample_file}")

        return df_enriched
    else:
        print("Failed to parse the spreadsheet.")
        return None


if __name__ == "__main__":
    dataframe = main()


def list_available_spreadsheets(downloads_folder="downloads"):
    """
    List all available spreadsheet files in the downloads folder.

    Args:
        downloads_folder (str): Path to the downloads folder (relative to script directory)

    Returns:
        list: List of file paths
    """
    # Get the absolute path to the script directory
    script_dir = Path(__file__).parent.absolute()
    downloads_path = script_dir / downloads_folder

    if not downloads_path.exists():
        return []

    file_patterns = ['*.xlsx', '*.xls', '*.csv']
    all_files = []

    for pattern in file_patterns:
        files = list(downloads_path.glob(pattern))
        all_files.extend(files)

    # Sort by modification time (most recent first)
    all_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    return [str(f) for f in all_files]


def parse_spreadsheet_to_dataframe(file_path, sheet_name=None):
    """
    Convert a spreadsheet file to a pandas DataFrame.

    Args:
        file_path (str): Path to the spreadsheet file
        sheet_name (str, optional): Name of the sheet to read (for Excel files)

    Returns:
        pd.DataFrame: The parsed data as a DataFrame
    """
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"Parsing spreadsheet: {file_path.name}")
        print(f"File size: {file_path.stat().st_size:,} bytes")

        # Determine file type and read accordingly
        file_extension = file_path.suffix.lower()

        if file_extension == '.csv':
            # Try different encodings for CSV files
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"Successfully read CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                raise ValueError(
                    "Could not read CSV file with any supported encoding")

        elif file_extension in ['.xlsx', '.xls']:
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"Read sheet: {sheet_name}")
            else:
                # Read the first sheet by default
                df = pd.read_excel(file_path)
                print("Read first sheet (default)")

        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        print(f"DataFrame shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
        print(f"Columns: {list(df.columns)}")

        return df

    except Exception as e:
        print(f"Error parsing spreadsheet: {e}")
        return None


def enrich_with_coordinates(df, postcode_column=None):
    """
    Enrich dataframe with longitude and latitude columns for postcodes.

    Args:
        df (pd.DataFrame): DataFrame containing postcode data
        postcode_column (str): Name of the postcode column (auto-detected if None)

    Returns:
        pd.DataFrame: DataFrame with added longitude and latitude columns
    """
    if df is None or df.empty:
        return df

    # Auto-detect postcode column if not specified
    if postcode_column is None:
        postcode_cols = [col for col in df.columns if 'postcode' in col.lower(
        ) or 'post code' in col.lower()]
        if not postcode_cols:
            print("No postcode column found - skipping coordinate enrichment")
            return df
        postcode_column = postcode_cols[0]

    print(f"Enriching coordinates for column: {postcode_column}")

    # Get unique postcodes to minimize API calls
    unique_postcodes = df[postcode_column].dropna().unique()
    print(f"Found {len(unique_postcodes)} unique postcodes to lookup")

    # Create coordinate lookup dictionary
    coord_cache = {}
    failed_lookups = 0

    for i, postcode in enumerate(unique_postcodes, 1):
        if pd.isna(postcode) or str(postcode).strip() == '':
            continue

        formatted_postcode = str(postcode).strip().upper()

        try:
            # Call postcodes.io API
            response = requests.get(
                f"https://api.postcodes.io/postcodes/{formatted_postcode}")

            if response.status_code == 200:
                data = response.json()
                if data['status'] == 200:
                    coord_cache[postcode] = {
                        'longitude': data['result']['longitude'],
                        'latitude': data['result']['latitude']
                    }
                else:
                    coord_cache[postcode] = {
                        'longitude': None, 'latitude': None}
                    failed_lookups += 1
            else:
                coord_cache[postcode] = {'longitude': None, 'latitude': None}
                failed_lookups += 1

        except Exception as e:
            print(f"Error looking up postcode {formatted_postcode}: {e}")
            coord_cache[postcode] = {'longitude': None, 'latitude': None}
            failed_lookups += 1

        # Show progress and rate limit
        if i % 10 == 0 or i == len(unique_postcodes):
            print(
                f"  Progress: {i}/{len(unique_postcodes)} postcodes processed")

        # Rate limiting - be respectful to the free API
        time.sleep(0.1)

    # Add coordinate columns to dataframe
    df['longitude'] = df[postcode_column].map(
        lambda pc: coord_cache.get(pc, {}).get('longitude'))
    df['latitude'] = df[postcode_column].map(
        lambda pc: coord_cache.get(pc, {}).get('latitude'))

    successful_lookups = len(unique_postcodes) - failed_lookups
    print(
        f"Coordinate enrichment complete: {successful_lookups}/{len(unique_postcodes)} successful lookups")

    return df


def explore_excel_sheets(file_path):
    """
    Explore all sheets in an Excel file.

    Args:
    """
    try:
        file_path = Path(file_path)

        if file_path.suffix.lower() not in ['.xlsx', '.xls']:
            print("This function only works with Excel files.")
            return {}

        # Get all sheet names
        excel_file = pd.ExcelFile(file_path)
        sheet_info = {}

        print(f"Excel file: {file_path.name}")
        print(f"Available sheets: {len(excel_file.sheet_names)}")
        print("-" * 50)

        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheet_info[sheet_name] = {
                    'rows': df.shape[0],
                    'columns': df.shape[1],
                    'column_names': list(df.columns)
                }

                print(f"Sheet: {sheet_name}")
                print(f"  Size: {df.shape[0]:,} rows × {df.shape[1]} columns")
                print(
                    f"  Columns: {list(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
                print()

            except Exception as e:
                print(f"Error reading sheet '{sheet_name}': {e}")
                sheet_info[sheet_name] = {'error': str(e)}

        return sheet_info

    except Exception as e:
        print(f"Error exploring Excel file: {e}")
        return {}


def display_dataframe_summary(df):
    """
    Display a summary of the DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to summarize
    """
    if df is None or df.empty:
        print("DataFrame is empty or None")
        return

    print("DataFrame Summary:")
    print("=" * 50)
    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print()

    print("Column Information:")
    print(df.info())
    print()

    print("First 5 rows:")
    print(df.head())
    print()

    print("Data types:")
    print(df.dtypes)
    print()

    # Check for missing values
    missing_values = df.isnull().sum()
    if missing_values.any():
        print("Missing values:")
        print(missing_values[missing_values > 0])
    else:
        print("No missing values found")


def main():
    """Main function to demonstrate the spreadsheet parsing functionality."""
    print("Licensed Competitions Tracker - Spreadsheet Parser")
    print("=" * 60)

    # Get the absolute path to the script directory
    script_dir = Path(__file__).parent.absolute()
    print(f"Script directory: {script_dir}")
    print()

    # List available spreadsheets
    available_files = list_available_spreadsheets()

    if not available_files:
        print("No spreadsheet files found in the downloads folder.")
        print("Please run DownloadSpreadsheet.py first to download a spreadsheet.")
        return

    print(f"Found {len(available_files)} spreadsheet file(s):")
    for i, file_path in enumerate(available_files, 1):
        file_name = Path(file_path).name
        file_size = Path(file_path).stat().st_size
        mod_time = datetime.fromtimestamp(Path(file_path).stat().st_mtime)
        print(
            f"  {i}. {file_name} ({file_size:,} bytes, modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')})")

    print()

    # Get the latest spreadsheet
    latest_file = get_latest_spreadsheet()
    print(f"Using latest file: {Path(latest_file).name}")
    print()

    # If it's an Excel file, explore sheets first
    if Path(latest_file).suffix.lower() in ['.xlsx', '.xls']:
        print("Exploring Excel sheets...")
        sheet_info = explore_excel_sheets(latest_file)
        print()

    # Parse the spreadsheet to DataFrame
    df = parse_spreadsheet_to_dataframe(latest_file)

    if df is not None:
        print()
        display_dataframe_summary(df)

        # Enrich with coordinates
        print("\n" + "=" * 60)
        print("ENRICHING WITH COORDINATES")
        print("=" * 60)
        df_enriched = enrich_with_coordinates(df)

        # Save a sample of the enriched data as CSV for inspection (using absolute path)
        script_dir = Path(__file__).parent.absolute()
        sample_file = script_dir / "parsed_data_sample.csv"
        sample_df = df_enriched.head(10) if len(
            df_enriched) > 10 else df_enriched
        sample_df.to_csv(sample_file, index=False)
        print(f"\nSaved enriched sample data to: {sample_file}")

        return df_enriched
    else:
        print("Failed to parse the spreadsheet.")
        return None


if __name__ == "__main__":
    dataframe = main()
