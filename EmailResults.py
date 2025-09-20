from FindCompetitions import find_name_column, find_competitions_within_distance, find_postcode_column
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
    Generate HTML email content for a user.

    Args:
        user_name (str): User's name
        user_email (str): User's email
        postcode (str): User's postcode
        max_distance (float): Maximum distance searched
        competitions_df (pd.DataFrame): Filtered competitions

    Returns:
        str: HTML email content
    """
    current_date = datetime.now().strftime("%B %d, %Y")

    # Start building HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Athletics Competitions</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .email-container {{
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 300;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
                font-size: 16px;
            }}
            .content {{
                padding: 30px;
            }}
            .greeting {{
                font-size: 18px;
                margin-bottom: 20px;
                color: #555;
            }}
            .search-info {{
                background-color: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 15px;
                margin: 20px 0;
                border-radius: 0 5px 5px 0;
            }}
            .competition {{
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin-bottom: 20px;
                overflow: hidden;
                transition: box-shadow 0.3s ease;
            }}
            .competition:hover {{
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }}
            .competition-header {{
                background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 15px 20px;
                border-bottom: 1px solid #dee2e6;
            }}
            .competition-name {{
                font-size: 18px;
                font-weight: 600;
                color: #495057;
                margin: 0;
            }}
            .competition-host {{
                font-size: 14px;
                font-weight: 400;
                color: #6c757d;
                margin: 0;
            }}
            .distance-badge {{
                display: inline-block;
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
                margin-top: 5px;
            }}
            .competition-details {{
                padding: 20px;
            }}
            .detail-row {{
                display: flex;
                margin-bottom: 10px;
                align-items: center;
            }}
            .detail-label {{
                font-weight: 600;
                color: #6c757d;
                width: 80px;
                flex-shrink: 0;
            }}
            .detail-value {{
                color: #495057;
                flex: 1;
            }}
            .summary {{
                background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
                text-align: center;
            }}
            .summary h3 {{
                margin: 0 0 15px 0;
                color: #495057;
            }}
            .stats {{
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
            }}
            .stat {{
                text-align: center;
                margin: 10px;
            }}
            .stat-number {{
                font-size: 24px;
                font-weight: 700;
                color: #667eea;
                display: block;
            }}
            .stat-label {{
                font-size: 14px;
                color: #6c757d;
                margin-top: 5px;
            }}
            .no-competitions {{
                text-align: center;
                padding: 40px;
                color: #6c757d;
            }}
            .no-competitions-icon {{
                font-size: 48px;
                margin-bottom: 20px;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
            }}
            .icon {{
                margin-right: 8px;
                color: #667eea;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>🏃‍♂️ Your Athletics Competitions</h1>
                <p>Licensed competitions near you • {current_date}</p>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Hello {user_name}! 👋
                </div>
                
                <div class="search-info">
                    <strong>Search Parameters:</strong><br>
                    📍 Your location: {postcode}<br>
                    📏 Maximum distance: {max_distance} miles
                </div>
    """

    if competitions_df is None or len(competitions_df) == 0:
        html += """
                <div class="no-competitions">
                    <div class="no-competitions-icon">😔</div>
                    <h3>No competitions found</h3>
                    <p>Sorry, we couldn't find any licensed athletics competitions within your specified distance.</p>
                    <p>Try increasing your maximum distance or check back later for new competitions.</p>
                </div>
        """
    else:
        # Add summary statistics
        distances = competitions_df['distance_miles'].dropna()
        html += f"""
                <div class="summary">
                    <h3>📊 Competition Summary</h3>
                    <div class="stats">
                        <div class="stat">
                            <span class="stat-number">{len(competitions_df)}</span>
                            <div class="stat-label">Total Found</div>
                        </div>
                        <div class="stat">
                            <span class="stat-number">{distances.min():.1f}</span>
                            <div class="stat-label">Closest (miles)</div>
                        </div>
                        <div class="stat">
                            <span class="stat-number">{distances.max():.1f}</span>
                            <div class="stat-label">Furthest (miles)</div>
                        </div>
                        <div class="stat">
                            <span class="stat-number">{distances.mean():.1f}</span>
                            <div class="stat-label">Average (miles)</div>
                        </div>
                    </div>
                </div>
                
                <h2>🏆 Your Competitions</h2>
        """

        # Add each competition
        name_col = find_name_column(competitions_df)
        host_cols = [
            col for col in competitions_df.columns if 'pot venue' in col.lower()]
        postcode_col = find_postcode_column(competitions_df)
        date_cols = [
            col for col in competitions_df.columns if 'date' in col.lower()]
        venue_cols = [col for col in competitions_df.columns if any(
            word in col.lower() for word in ['venue', 'location', 'place'])]
        level_cols = [col for col in competitions_df.columns if 'level' in col.lower(
        ) or 'licence' in col.lower()]
        link_cols = [col for col in competitions_df.columns if 'link' in col.lower(
        ) or 'url' in col.lower() or 'wpa endorsed' in col.lower()]

        for i, (_, row) in enumerate(competitions_df.iterrows(), 1):
            distance = row['distance_miles']

            if name_col and pd.notna(row[name_col]):
                name = str(row[name_col])
            else:
                name = f"Competition {i}"

            if host_cols and pd.notna(row[host_cols[0]]):
                host = str(row[host_cols[0]])
            else:
                host = "Unkown Host"

            html += f"""
                <div class="competition">
                    <div class="competition-header">
                        <div class="competition-name">{name}</div>
                        <div class="competition-host">{host}</div>
                        <span class="distance-badge">📍 {distance:.1f} miles away</span>
                    </div>
                    <div class="competition-details">
            """

            links = create_search_links(name, venue=row[venue_cols[0]] if venue_cols and pd.notna(
                row[venue_cols[0]]) else None, location=row[postcode_col] if postcode_col and pd.notna(row[postcode_col]) else None)

            # Add date if available
            if date_cols and pd.notna(row[date_cols[0]]):
                date_str = str(row[date_cols[0]])
                if '00:00:00' in date_str:
                    date_str = date_str.split(' ')[0]
                html += f"""
                        <div class="detail-row">
                            <span class="detail-label icon">📅</span>
                            <span class="detail-value">{date_str}</span>
                        </div>
                """

            has_venue = venue_cols and pd.notna(row[venue_cols[0]])
            has_postcode = postcode_col and pd.notna(row[postcode_col])
            # Add venue if available
            if has_venue and not has_postcode:
                html += f"""
                        <div class="detail-row">
                            <span class="detail-label icon">🏟️</span>
                            <span class="detail-value"><a href="{links['google_maps']}">{row[venue_cols[0]]}</a></span>
                        </div>
                """
            # Add postcode if available
            if has_venue and has_postcode:
                html += f"""
                        <div class="detail-row">
                            <span class="detail-label icon">🏟️</span>
                            <span class="detail-value"><a href="{links['google_maps']}">{row[venue_cols[0]]} ({row[postcode_col]})</a></span>
                        </div>
                """

            # Add link if available
            if link_cols and pd.notna(row[link_cols[0]]):
                html += f"""
                        <div class="detail-row">
                            <span class="detail-label icon">🔗</span>
                            <span class="detail-value"><a href="{row[link_cols[0]]}">View Competition</a></span>
                        </div>
                """
            else:
                html += f"""
                        <div class="detail-row">
                            <span class="detail-label icon">🔗</span>
                            <span class="detail-value"><a href="{links['google']}">Search Google</a></span>
                        </div>
                """

            # Add level if available
            if level_cols and pd.notna(row[level_cols[0]]):
                html += f"""
                        <div class="detail-row">
                            <span class="detail-label icon">🏅</span>
                            <span class="detail-value">Level {row[level_cols[0]]} Competition</span>
                        </div>
                """

            html += """
                    </div>
                </div>
            """

    # Close HTML
    html += f"""
            </div>
            
            <div class="footer">
                <p>Generated on {current_date} by Licensed Competitions Tracker</p>
                <p>Data sourced from England Athletics</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


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

    for i, (_, user) in enumerate(users_df.iterrows(), 1):
        user_name = user['Name']
        user_email = user['Email']
        postcode = str(user['Postcode']).replace(
            ' ', ' ').upper()  # Format postcode
        max_distance = float(user['MaxDistance'])

        print(f"Processing user {i}/{len(users_df)}: {user_name} ({postcode})")

        # Get competitions for this user
        competitions = find_competitions_within_distance(
            postcode, max_distance)

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
