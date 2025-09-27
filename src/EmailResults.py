from FindCompetitions import find_name_column, find_competitions_within_distance, find_postcode_column, load_competition_data
from EmailTemplateManager import EmailTemplateManager
from dotenv import load_dotenv
import os
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import pandas as pd

# Load environment variables from .env file
load_dotenv()


def load_email_config():
    """
    Load email configuration from .env file.

    Returns:
        dict: Email configuration or None if not available
    """
    config = {
        'smtp_server': os.getenv('SMTP_SERVER'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'username': os.getenv('EMAIL_USERNAME'),
        'password': os.getenv('EMAIL_PASSWORD'),
        'from_name': os.getenv('FROM_NAME', 'Athletics Competitions Tracker'),
        'reply_to': os.getenv('REPLY_TO'),
        'send_emails': os.getenv('SEND_EMAILS', 'False').lower() == 'true'
    }

    # Check if required fields are available
    if not all([config['smtp_server'], config['username'], config['password']]):
        return None

    return config


def load_user_data(csv_file="UserData.csv"):
    """
    Load user data from CSV file.

    Args:
        csv_file (str): Path to the user data CSV file

    Returns:
        pd.DataFrame: User data or None if error
    """
    try:
        script_dir = Path(__file__).parent.absolute()
        csv_path = script_dir / csv_file

        if not csv_path.exists():
            print(f"User data file not found: {csv_path}")
            return None

        df = pd.read_csv(csv_path)

        # Validate required columns
        required_cols = ['Name', 'Email', 'Postcode', 'MaxDistance']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"Missing required columns in CSV: {missing_cols}")
            return None

        print(f"Loaded {len(df)} users from {csv_file}")
        return df

    except Exception as e:
        print(f"Error loading user data: {e}")
        return None


def create_search_links(competition_name, venue=None, location=None):
    """
    Create multiple search links for a competition.

    Args:
        competition_name (str): Name of the competition
        venue (str): Venue name
        location (str): Location name

    Returns:
        dict: Dictionary with different search URLs (google, google maps, bing, athletics weekly, runbritain)
    """
    import urllib.parse

    # Build google search query
    search_terms = [competition_name]
    if venue:
        search_terms.append(venue)
    if location:
        search_terms.append(location)
    search_terms.append("athletics")

    search_query = " ".join(search_terms)
    encoded_query = urllib.parse.quote_plus(search_query)

    # Build maps search query
    search_terms = []
    if not venue and not location:
        search_terms.append(competition_name)
    if venue:
        search_terms.append(venue)
    if location:
        search_terms.append(location)

    search_query = " ".join(search_terms)
    maps_encoded_query = urllib.parse.quote_plus(search_query)

    return {
        'google': f"https://www.google.com/search?q={encoded_query}",
        'google_maps': f"https://www.google.com/maps/search/{maps_encoded_query}",
        'bing': f"https://www.bing.com/search?q={encoded_query}",
        'athletics_weekly': f"https://www.google.com/search?q={encoded_query}+site:athleticsweekly.com",
        'runbritain': f"https://www.google.com/search?q={encoded_query}+site:runbritain.com"
    }


def generate_html_email(user_name, user_email, postcode, max_distance, competitions_df):
    """
    Generate HTML email content for a user using templates.

    Args:
        user_name (str): User's name
        user_email (str): User's email
        postcode (str): User's postcode
        max_distance (float): Maximum distance searched
        competitions_df (pd.DataFrame): Filtered competitions

    Returns:
        str: HTML email content
    """
    template_manager = EmailTemplateManager()
    current_date = datetime.now().strftime("%B %d, %Y")

    if competitions_df is None or len(competitions_df) == 0:
        competitions_content = template_manager.render_no_competitions()
    else:
        # Generate summary statistics
        competitions_content = template_manager.render_summary_stats(
            competitions_df)
        competitions_content += "\n<h2>🏆 Your Competitions</h2>\n"

        # Find column mappings
        name_col = find_name_column(competitions_df)
        host_cols = [
            col for col in competitions_df.columns if 'pot venue' in col.lower()]
        postcode_col = find_postcode_column(competitions_df)
        date_cols = [
            col for col in competitions_df.columns if 'date' in col.lower()]
        venue_cols = [col for col in competitions_df.columns if any(
            word in col.lower() for word in ['venue', 'location', 'place'])]
        level_cols = [col for col in competitions_df.columns if 'level' in col.lower()
                      or 'licence' in col.lower()]
        link_cols = [col for col in competitions_df.columns if 'link' in col.lower()
                     or 'url' in col.lower() or 'wpa endorsed' in col.lower()]

        # Generate each competition card
        for i, (_, row) in enumerate(competitions_df.iterrows(), 1):
            distance = row['distance_miles']

            # Get competition name and host
            name = str(row[name_col]) if name_col and pd.notna(
                row[name_col]) else f"Competition {i}"
            host = str(row[host_cols[0]]) if host_cols and pd.notna(
                row[host_cols[0]]) else "Unknown Host"

            # Generate competition details
            details_html = generate_competition_details(row, venue_cols, postcode_col,
                                                        date_cols, link_cols, level_cols,
                                                        template_manager)

            # Render the competition card
            competition_card = template_manager.render_competition_card(
                name, host, distance, details_html)
            competitions_content += competition_card

    # Render the complete email
    return template_manager.render_full_email(
        user_name=user_name,
        postcode=postcode,
        max_distance=max_distance,
        competitions_content=competitions_content,
        current_date=current_date
    )


def generate_competition_details(row, venue_cols, postcode_col, date_cols, link_cols, level_cols, template_manager):
    """
    Generate HTML for competition details section.

    Args:
        row: DataFrame row with competition data
        venue_cols, postcode_col, date_cols, link_cols, level_cols: Column references
        template_manager: EmailTemplateManager instance

    Returns:
        str: HTML for competition details
    """
    details_html = ""

    # Get venue and location info
    venue = row[venue_cols[0]] if venue_cols and pd.notna(
        row[venue_cols[0]]) else None
    location = row[postcode_col] if postcode_col and pd.notna(
        row[postcode_col]) else None

    # Get competition name for search links
    name_col = find_name_column(pd.DataFrame([row]))
    comp_name = str(row[name_col]) if name_col and pd.notna(
        row[name_col]) else "Competition"

    # Create search links
    links = create_search_links(comp_name, venue, location)

    # Add date if available
    if date_cols and pd.notna(row[date_cols[0]]):
        date_str = str(row[date_cols[0]])
        if '00:00:00' in date_str:
            date_str = date_str.split(' ')[0]
        details_html += template_manager.render_detail_row(
            "�", "Date", date_str)

    # Add venue/location
    if venue and location:
        venue_text = f"{venue} ({location})"
        details_html += template_manager.render_detail_row(
            "🏟️", "Venue", venue_text, links['google_maps'])
    elif venue:
        details_html += template_manager.render_detail_row(
            "🏟️", "Venue", venue, links['google_maps'])

    # Add competition link or search link
    if link_cols and pd.notna(row[link_cols[0]]):
        details_html += template_manager.render_detail_row(
            "🔗", "Info", "View Competition", row[link_cols[0]])
    else:
        details_html += template_manager.render_detail_row(
            "🔍", "Search", "Search Google", links['google'])

    # Add level if available
    if level_cols and pd.notna(row[level_cols[0]]):
        details_html += template_manager.render_detail_row(
            "🏅", "Level", f"Level {row[level_cols[0]]} Competition")

    return details_html


def save_email_to_file(user_name, html_content):
    """
    Save HTML email to a file.

    Args:
        user_name (str): User's name for filename
        html_content (str): HTML email content

    Returns:
        str: Path to saved file
    """
    script_dir = Path(__file__).parent.absolute()
    filename = f"email_{user_name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    file_path = script_dir / "emails" / filename

    # Create emails directory if it doesn't exist
    file_path.parent.mkdir(exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return str(file_path)


def send_email(to_email, subject, html_content, smtp_server=None, smtp_port=587, username=None, password=None, from_name=None):
    """
    Send HTML email using configuration from .env file.

    Args:
        to_email (str): Recipient email
        subject (str): Email subject
        html_content (str): HTML email content
        smtp_server (str): SMTP server (e.g., 'smtp.gmail.com')
        smtp_port (int): SMTP port
        username (str): SMTP username
        password (str): SMTP password
        from_name (str): Display name for sender

    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not all([smtp_server, username, password]):
        print("SMTP configuration not provided. Skipping email send.")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject

        # Set From header with optional display name
        if from_name:
            msg['From'] = f"{from_name} <{username}>"
        else:
            msg['From'] = username

        msg['To'] = to_email

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False


def show_env_example():
    """Show example .env configuration."""
    print("📧 Email Configuration (.env file example):")
    print("=" * 50)
    print("""# SMTP Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Email Settings
FROM_NAME=Athletics Competitions Tracker
REPLY_TO=your_email@gmail.com

# Enable/disable actual email sending
SEND_EMAILS=true

# For Gmail users:
# 1. Enable 2-factor authentication
# 2. Generate an App Password (not your regular password)
# 3. Use the App Password in EMAIL_PASSWORD
""")


def process_all_users():
    """
    Process all users in the CSV file and generate emails.
    """
    print("Licensed Competitions Tracker - Email Results Generator")
    print("=" * 60)

    # Check email configuration
    email_config = load_email_config()
    if email_config:
        if email_config['send_emails']:
            print(f"📧 Email sending: ENABLED")
            print(
                f"📧 SMTP Server: {email_config['smtp_server']}:{email_config['smtp_port']}")
            print(
                f"📧 From: {email_config['from_name']} <{email_config['username']}>")
        else:
            print(f"📧 Email sending: DISABLED (SEND_EMAILS=False in .env)")
    else:
        print(f"⚠️  Email configuration not found in .env file")
        print(f"📧 Emails will be saved as HTML files only")

        # Ask if user wants to see example
        show_example = input(
            "\nWould you like to see an example .env configuration? (y/n): ").strip().lower()
        if show_example == 'y':
            show_env_example()

    print()

    # Load user data
    users_df = load_user_data()
    if users_df is None:
        return

    print(f"Processing {len(users_df)} users...")
    print()

    # Load latest competition data
    df = load_competition_data()

    for i, (_, user) in enumerate(users_df.iterrows(), 1):
        user_name = user['Name']
        user_email = user['Email']
        postcode = str(user['Postcode']).replace(
            ' ', ' ').upper()  # Format postcode
        max_distance = float(user['MaxDistance'])

        print(f"Processing user {i}/{len(users_df)}: {user_name} ({postcode})")

        # Get competitions for this user
        competitions = find_competitions_within_distance(
            df, postcode, max_distance)

        # Generate HTML email
        html_content = generate_html_email(
            user_name, user_email, postcode, max_distance, competitions)

        # Save email to file
        email_file = save_email_to_file(user_name, html_content)
        print(f"  ✅ Email saved to: {email_file}")

        # Send email if configuration is available
        email_config = load_email_config()
        if email_config and email_config['send_emails']:
            sent = send_email(
                to_email=user_email,
                subject="Your Licensed Athletics Competitions",
                html_content=html_content,
                smtp_server=email_config['smtp_server'],
                smtp_port=email_config['smtp_port'],
                username=email_config['username'],
                password=email_config['password'],
                from_name=email_config['from_name']
            )

            if sent:
                print(f"  📧 Email sent successfully to {user_email}")
            else:
                print(f"  ❌ Failed to send email to {user_email}")
        else:
            if email_config is None:
                print(f"  ⚠️  Email configuration not available in .env file")
            else:
                print(f"  📧 Email sending disabled (SEND_EMAILS=False in .env)")

        # Show summary
        if competitions is not None and len(competitions) > 0:
            print(
                f"  📍 Found {len(competitions)} competitions within {max_distance} miles")
        else:
            print(f"  📍 No competitions found within {max_distance} miles")

        print()

    print("All emails generated successfully!")
    print(
        f"Email files saved in: {Path(__file__).parent.absolute() / 'emails'}")


def main():
    """Main function."""
    try:
        process_all_users()

    except KeyboardInterrupt:
        print("\n\nProcess cancelled by user.")


if __name__ == "__main__":
    main()
