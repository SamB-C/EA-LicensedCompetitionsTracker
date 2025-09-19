import requests
import pandas as pd
import math
from pathlib import Path
import time


class PostcodeDistanceCalculator:
    """Calculate distances between postcodes using geolocation APIs."""

    def __init__(self, base_postcode=None):
        """
        Initialize the distance calculator.

        Args:
            base_postcode (str): Your home/base postcode for distance calculations
        """
        self.base_postcode = base_postcode
        self.base_coords = None

        if base_postcode:
            self.base_coords = self.get_postcode_coordinates(base_postcode)

    def get_postcode_coordinates(self, postcode):
        """
        Get latitude and longitude for a UK postcode using postcodes.io API (free).

        Args:
            postcode (str): UK postcode

        Returns:
            tuple: (latitude, longitude) or None if not found
        """
        try:
            # Clean the postcode
            postcode = postcode.strip().replace(' ', '').upper()

            # Use postcodes.io - free UK postcode API
            url = f"https://api.postcodes.io/postcodes/{postcode}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data['status'] == 200:
                    result = data['result']
                    return (result['latitude'], result['longitude'])

            print(f"Could not find coordinates for postcode: {postcode}")
            return None

        except Exception as e:
            print(f"Error getting coordinates for {postcode}: {e}")
            return None

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points on Earth.

        Args:
            lat1, lon1: Latitude and longitude of first point
            lat2, lon2: Latitude and longitude of second point

        Returns:
            float: Distance in miles
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * \
            math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        # Earth's radius in miles
        r = 3956

        return c * r

    def calculate_distance_to_postcode(self, target_postcode):
        """
        Calculate distance from base postcode to target postcode.

        Args:
            target_postcode (str): Postcode to calculate distance to

        Returns:
            float: Distance in miles, or None if calculation fails
        """
        if not self.base_coords:
            print("No base postcode set. Please initialize with a base postcode.")
            return None

        target_coords = self.get_postcode_coordinates(target_postcode)
        if not target_coords:
            return None

        distance = self.haversine_distance(
            self.base_coords[0], self.base_coords[1],
            target_coords[0], target_coords[1]
        )

        return round(distance, 1)

    def add_distances_to_dataframe(self, df, postcode_column, distance_column='distance_miles'):
        """
        Add distance calculations to a DataFrame containing postcodes.

        Args:
            df (pd.DataFrame): DataFrame with postcode column
            postcode_column (str): Name of the column containing postcodes
            distance_column (str): Name of the new column for distances

        Returns:
            pd.DataFrame: DataFrame with added distance column
        """
        if not self.base_coords:
            print("No base postcode set. Cannot calculate distances.")
            return df

        if postcode_column not in df.columns:
            print(f"Column '{postcode_column}' not found in DataFrame.")
            return df

        print(f"Calculating distances from {self.base_postcode}...")
        print(f"Processing {len(df)} rows...")

        distances = []

        for i, postcode in enumerate(df[postcode_column], 1):
            if pd.isna(postcode) or postcode == '':
                distances.append(None)
            else:
                distance = self.calculate_distance_to_postcode(str(postcode))
                distances.append(distance)

                # Progress indicator
                if i % 10 == 0:
                    print(f"Processed {i}/{len(df)} postcodes...")

                # Be nice to the API - small delay
                time.sleep(0.1)

        df[distance_column] = distances

        # Show summary
        valid_distances = [d for d in distances if d is not None]
        if valid_distances:
            print(f"\nDistance calculation complete!")
            print(f"Successfully calculated {len(valid_distances)} distances")
            print(f"Closest: {min(valid_distances):.1f} miles")
            print(f"Furthest: {max(valid_distances):.1f} miles")
            print(
                f"Average: {sum(valid_distances)/len(valid_distances):.1f} miles")

        return df


def demo_with_competitions_data():
    """Demonstrate distance calculation with competitions data."""

    # You'll need to set your home postcode here
    HOME_POSTCODE = "SW1A 2AA"  # Example London postcode - change this to your postcode

    print("Postcode Distance Calculator Demo")
    print("=" * 50)

    # Initialize calculator
    calc = PostcodeDistanceCalculator(HOME_POSTCODE)

    if not calc.base_coords:
        print(f"Could not find coordinates for base postcode: {HOME_POSTCODE}")
        print("Please check the postcode and try again.")
        return

    print(f"Base location: {HOME_POSTCODE}")
    print(f"Coordinates: {calc.base_coords[0]:.4f}, {calc.base_coords[1]:.4f}")
    print()

    # Try to load competitions data
    try:
        from ParseSpreadsheet import get_latest_spreadsheet, parse_spreadsheet_to_dataframe

        latest_file = get_latest_spreadsheet()
        if latest_file:
            df = parse_spreadsheet_to_dataframe(latest_file)

            if df is not None and len(df) > 0:
                print("Loaded competitions data:")
                print(f"Columns: {list(df.columns)}")
                print()

                # Look for postcode-related columns
                postcode_columns = [
                    col for col in df.columns if 'postcode' in col.lower() or 'post' in col.lower()]

                if postcode_columns:
                    postcode_col = postcode_columns[0]
                    print(f"Found postcode column: {postcode_col}")

                    # Show sample of postcodes
                    sample_postcodes = df[postcode_col].dropna().head(5)
                    print(f"Sample postcodes: {list(sample_postcodes)}")
                    print()

                    # Calculate distances for first 20 rows (for demo)
                    demo_df = df.head(20).copy()
                    demo_df_with_distances = calc.add_distances_to_dataframe(
                        demo_df, postcode_col)

                    # Show results
                    print("\nSample results:")
                    relevant_cols = [col for col in demo_df_with_distances.columns if col in [
                        postcode_col, 'distance_miles'] or 'name' in col.lower() or 'event' in col.lower()]
                    print(demo_df_with_distances[relevant_cols].head(10))

                    # Save results
                    script_dir = Path(__file__).parent.absolute()
                    output_file = script_dir / "competitions_with_distances.csv"
                    demo_df_with_distances.to_csv(output_file, index=False)
                    print(f"\nSaved results to: {output_file}")

                else:
                    print("No postcode columns found in the data.")
                    print("Available columns:", list(df.columns))
            else:
                print("Could not load competitions data.")
        else:
            print("No spreadsheet files found. Run DownloadSpreadsheet.py first.")

    except ImportError:
        print("ParseSpreadsheet module not found. Testing with sample data...")
        test_sample_distances(calc)


def test_sample_distances(calc):
    """Test with some sample postcodes."""
    sample_postcodes = [
        "SW1A 1AA",  # London
        "M1 1AA",    # Manchester
        "B1 1AA",    # Birmingham
        "LS1 1AA",   # Leeds
        "NE1 1AA"    # Newcastle
    ]

    print("Testing with sample postcodes:")
    for postcode in sample_postcodes:
        distance = calc.calculate_distance_to_postcode(postcode)
        if distance:
            print(f"{postcode}: {distance} miles")
        else:
            print(f"{postcode}: Could not calculate distance")


if __name__ == "__main__":
    demo_with_competitions_data()
