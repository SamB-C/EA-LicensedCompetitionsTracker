import pandas as pd
from pathlib import Path
import sys
from PostCodeDistanceCalc import PostcodeDistanceCalculator
from ParseSpreadsheet import get_latest_spreadsheet, parse_spreadsheet_to_dataframe


def get_user_input():
    """
    Get postcode and maximum distance from user.

    Returns:
        tuple: (postcode, max_distance) or (None, None) if invalid input
    """
    print("Find Competitions Near You")
    print("=" * 30)

    # Get postcode
    while True:
        postcode = input("Enter your postcode: ").strip().upper()
        if not postcode:
            print("Please enter a valid postcode.")
            continue

        # Basic validation - UK postcodes are typically 6-8 characters
        if len(postcode) < 5 or len(postcode) > 8:
            print("Please enter a valid UK postcode (e.g., SW1A 1AA).")
            continue

        break

    # Get maximum distance
    while True:
        try:
            distance_input = input("Enter maximum distance in miles: ").strip()
            max_distance = float(distance_input)

            if max_distance <= 0:
                print("Distance must be greater than 0.")
                continue

            if max_distance > 500:
                print("That seems quite far! Are you sure? (y/n): ", end="")
                confirm = input().strip().lower()
                if confirm != 'y':
                    continue

            break

        except ValueError:
            print("Please enter a valid number for distance.")

    return postcode, max_distance


def find_postcode_column(df):
    """
    Find the column that likely contains postcodes.

    Args:
        df (pd.DataFrame): The competitions dataframe

    Returns:
        str: Column name or None if not found
    """
    # Look for columns with postcode-related names
    postcode_keywords = ['postcode', 'post_code',
                         'postal_code', 'post code', 'zip']

    for col in df.columns:
        col_lower = col.lower()
        for keyword in postcode_keywords:
            if keyword in col_lower:
                return col

    return None


def find_name_column(df):
    """
    Find the column that likely contains competition names.

    Args:
        df (pd.DataFrame): The competitions dataframe

    Returns:
        str: Column name or None if not found
    """
    # Look for columns with name-related keywords
    name_keywords = ['name', 'title', 'event', 'competition', 'meeting']

    for col in df.columns:
        col_lower = col.lower()
        for keyword in name_keywords:
            if keyword in col_lower:
                return col

    # If no obvious name column, return the first column
    return df.columns[0] if len(df.columns) > 0 else None


def find_competitions_within_distance(postcode, max_distance):
    """
    Find all competitions within the specified distance of the postcode.

    Args:
        postcode (str): User's postcode
        max_distance (float): Maximum distance in miles

    Returns:
        pd.DataFrame: Filtered competitions data or None if error
    """
    print(
        f"\nSearching for competitions within {max_distance} miles of {postcode}...")

    # Initialize distance calculator
    calc = PostcodeDistanceCalculator(postcode)

    if not calc.base_coords:
        print(f"Could not find coordinates for postcode: {postcode}")
        print("Please check the postcode is valid and try again.")
        return None

    print(
        f"Your location coordinates: {calc.base_coords[0]:.4f}, {calc.base_coords[1]:.4f}")

    # Load competitions data
    latest_file = get_latest_spreadsheet()
    if not latest_file:
        print("No spreadsheet files found in downloads folder.")
        print("Please run DownloadSpreadsheet.py first to download competition data.")
        return None

    print(f"Loading data from: {Path(latest_file).name}")
    df = parse_spreadsheet_to_dataframe(latest_file)

    if df is None or len(df) == 0:
        print("Could not load competition data.")
        return None

    print(f"Loaded {len(df)} competitions")

    # Find postcode column
    postcode_col = find_postcode_column(df)
    if not postcode_col:
        print("Could not find postcode column in the data.")
        print(f"Available columns: {list(df.columns)}")
        return None

    print(f"Using postcode column: {postcode_col}")

    # Calculate distances
    print("Calculating distances...")
    df_with_distances = calc.add_distances_to_dataframe(df, postcode_col)

    # Filter competitions within distance
    within_distance = df_with_distances[
        (df_with_distances['distance_miles'].notna()) &
        (df_with_distances['distance_miles'] <= max_distance)
    ].copy()

    # Sort by distance
    within_distance = within_distance.sort_values('distance_miles')

    return within_distance


def display_results(competitions_df, max_distance):
    """
    Display the filtered competition results.

    Args:
        competitions_df (pd.DataFrame): Filtered competitions data
        max_distance (float): Maximum distance searched
    """
    if competitions_df is None or len(competitions_df) == 0:
        print(f"\nNo competitions found within {max_distance} miles.")
        return

    print(
        f"\nFound {len(competitions_df)} competitions within {max_distance} miles:")
    print("=" * 60)

    # Find name column
    name_col = find_name_column(competitions_df)

    # Display results
    for i, (_, row) in enumerate(competitions_df.iterrows(), 1):
        distance = row['distance_miles']

        if name_col and pd.notna(row[name_col]):
            name = str(row[name_col])
        else:
            name = "Competition name not available"

        print(f"{i:2d}. {name}")
        print(f"    Distance: {distance:.1f} miles")

        # Show additional relevant info if available
        date_cols = [
            col for col in competitions_df.columns if 'date' in col.lower()]
        venue_cols = [col for col in competitions_df.columns if any(
            word in col.lower() for word in ['venue', 'location', 'place'])]

        if date_cols and pd.notna(row[date_cols[0]]):
            print(f"    Date: {row[date_cols[0]]}")

        if venue_cols and pd.notna(row[venue_cols[0]]):
            print(f"    Venue: {row[venue_cols[0]]}")

        print()

    # Summary statistics
    distances = competitions_df['distance_miles'].dropna()
    if len(distances) > 0:
        print(f"Distance summary:")
        print(f"  Closest: {distances.min():.1f} miles")
        print(f"  Furthest: {distances.max():.1f} miles")
        print(f"  Average: {distances.mean():.1f} miles")


def save_results(competitions_df, postcode, max_distance):
    """
    Save the results to a CSV file.

    Args:
        competitions_df (pd.DataFrame): Filtered competitions data
        postcode (str): User's postcode
        max_distance (float): Maximum distance
    """
    if competitions_df is None or len(competitions_df) == 0:
        return

    # Create filename
    postcode_clean = postcode.replace(' ', '').replace('/', '_')
    filename = f"competitions_near_{postcode_clean}_within_{max_distance}miles.csv"

    script_dir = Path(__file__).parent.absolute()
    output_path = script_dir / filename

    # Save to CSV
    competitions_df.to_csv(output_path, index=False)
    print(f"\nResults saved to: {output_path}")


def main():
    """Main function to find competitions near a postcode."""
    try:
        # Get user input
        postcode, max_distance = get_user_input()

        if not postcode or not max_distance:
            print("Invalid input. Exiting.")
            return

        # Find competitions
        competitions = find_competitions_within_distance(
            postcode, max_distance)

        # Display results
        display_results(competitions, max_distance)

        # Ask if user wants to save results
        if competitions is not None and len(competitions) > 0:
            save_choice = input(
                "\nWould you like to save these results to a CSV file? (y/n): ").strip().lower()
            if save_choice == 'y':
                save_results(competitions, postcode, max_distance)

        print("\nSearch complete!")

    except KeyboardInterrupt:
        print("\n\nSearch cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check your inputs and try again.")


if __name__ == "__main__":
    main()
