from EmailTemplateManager import EmailTemplateManager
from ParseSpreadsheet import parse_spreadsheet_to_dataframe, enrich_with_coordinates
from PostCodeDistanceCalc import PostcodeDistanceCalculator
import os
import sys
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


def get_users_from_supabase():
    """Get all active users from Supabase."""
    supabase_url = os.environ['SUPABASE_URL']
    service_key = os.environ['SUPABASE_SERVICE_KEY']

    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }

    response = requests.get(
        f"{supabase_url}/rest/v1/competition_users?active=eq.true",
        headers=headers
    )
    response.raise_for_status()

    return response.json()


def download_competitions_data():
    """Download and parse the latest competitions data."""
    print("Downloading latest competition data from England Athletics...")

    # This is a simplified version - you'll need to implement the actual
    # download logic from your DownloadSpreadsheet.py
    url = "https://www.englandathletics.org/athletics-and-running/england-athletics-facilities-and-clubs/track-and-field-facilities/licensed-facilities/"

    # For now, return None and handle gracefully
    # You'll need to implement the actual download and parsing logic
    print("⚠️  Note: Automatic download not implemented yet.")
    print("   You may need to manually update the data source.")

    return None


def send_email_via_mailgun(to_email, subject, html_content):
    """Send email using Mailgun."""
    mailgun_domain = os.environ['MAILGUN_DOMAIN']
    api_key = os.environ['MAILGUN_API_KEY']
    from_email = os.environ.get(
        'FROM_EMAIL', f'Athletics Tracker <noreply@{mailgun_domain}>')

    response = requests.post(
        f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
        auth=("api", api_key),
        data={
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "html": html_content
        }
    )
    response.raise_for_status()
    return response


def process_user(user, competitions_df, template_manager):
    """Process a single user and send their email."""
    try:
        postcode = user['postcode']
        max_distance = user['max_distance']

        print(
            f"Processing {user['name']} ({user['email']}) - {postcode}, {max_distance} miles")

        # Find competitions within distance
        calc = PostcodeDistanceCalculator(postcode)
        if not calc.base_coords:
            print(f"  ⚠️  Could not find coordinates for {postcode}")
            return False

        # Add distances to dataframe
        df_with_distances = calc.add_distances_to_dataframe(competitions_df)

        # Filter competitions within distance
        competitions = df_with_distances[
            (df_with_distances['distance_miles'].notna()) &
            (df_with_distances['distance_miles'] <= max_distance)
        ].copy()

        competitions = competitions.sort_values('distance_miles')

        # Generate email HTML
        html_content = template_manager.generate_html_email(
            user['name'],
            user['email'],
            postcode,
            max_distance,
            competitions
        )

        # Send email
        subject = f"Your Monthly Athletics Competitions - {datetime.now().strftime('%B %Y')}"
        send_email_via_mailgun(user['email'], subject, html_content)

        print(
            f"  ✅ Email sent successfully ({len(competitions)} competitions found)")
        return True

    except Exception as e:
        print(f"  ❌ Failed to process {user['email']}: {e}")
        return False


def main():
    """Main function to send monthly emails."""
    try:
        print("🏃‍♂️ Starting Monthly Competition Email Job")
        print("=" * 50)

        # Get users from Supabase
        print("📊 Getting users from database...")
        users = get_users_from_supabase()
        print(f"Found {len(users)} active users")

        if not users:
            print("No active users found. Exiting.")
            return

        # Download competition data
        competitions_df = download_competitions_data()
        competitions_df = enrich_with_coordinates(competitions_df)
        if competitions_df is None:
            print("❌ Could not load competition data. Exiting.")
            # For now, create a dummy DataFrame for testing
            print("ℹ️  Using dummy data for testing...")
            competitions_df = pd.DataFrame({
                'Competition Name': ['Test Competition'],
                'POST CODE': ['SW1A 1AA'],
                'Date': ['2024-01-15'],
                'Venue': ['Test Venue'],
                'latitude': [51.5074],
                'longitude': [-0.1278]
            })

        # Initialize template manager
        template_manager = EmailTemplateManager()

        # Process each user
        print("\n📧 Sending emails...")
        successful_sends = 0
        failed_sends = 0

        for user in users:
            if process_user(user, competitions_df, template_manager):
                successful_sends += 1
            else:
                failed_sends += 1

        # Summary
        print("\n📊 Summary:")
        print(f"✅ Successful sends: {successful_sends}")
        print(f"❌ Failed sends: {failed_sends}")
        print(f"📧 Total processed: {len(users)}")

        print("\n🎉 Monthly email job completed!")

    except Exception as e:
        print(f"❌ Critical error in main process: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
