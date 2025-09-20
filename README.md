# 🏃‍♂️ Licensed Competitions Tracker

A comprehensive Python-based tool for tracking and finding licensed athletics competitions near you. This application downloads competition data from England Athletics, calculates distances from your location, and can automatically send personalized email reports with nearby competitions.

## ✨ Features

- **🔄 Automatic Data Download**: Downloads the latest licensed competitions data from England Athletics
- **📍 Distance Calculation**: Uses UK postcode data to calculate distances to competition venues
- **🔍 Competition Search**: Find competitions within a specified distance from your location
- **📧 Email Reports**: Generate and send beautiful HTML email reports with nearby competitions
- **👥 Multi-User Support**: Support for multiple users with different locations and distance preferences
- **🔗 Search Links**: Direct links to Google searches, and maps.
- **💾 Data Export**: Save results to CSV files for further analysis

## 📋 Requirements

- Python 3.7 or higher
- Internet connection for downloading data and API calls
- Email account with SMTP access (optional, for email features)

## 🔧 Installation

### 1. Clone or Download the Project

```bash
git clone https://github.com/SamB-C/EA-LicensedCompetitionsTracker.git
cd LicensedCompetitionsTracker
```

### 2. Create a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Required Packages

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests pandas python-dotenv openpyxl xlrd
```

### 4. Set Up Email Configuration (Optional)

Create a `.env` file in the project root directory:

```bash
# SMTP Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Email Settings
FROM_NAME=Athletics Competitions Tracker
REPLY_TO=your_email@gmail.com

# Enable/disable actual email sending
SEND_EMAILS=true
```

#### Email Provider Settings:

**Gmail:**

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
# Note: Use App Password, not regular password
```

**iCloud:**

```bash
SMTP_SERVER=smtp.mail.me.com
SMTP_PORT=587
# Note: Use App-Specific Password
```

**Outlook/Hotmail:**

```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

#### Setting Up App Passwords:

**For Gmail:**

1. Enable 2-factor authentication on your Google account
2. Go to Google Account settings > Security
3. Generate an App Password
4. Use the generated password in `EMAIL_PASSWORD`

**For iCloud:**

1. Enable 2-factor authentication on your Apple ID
2. Go to appleid.apple.com > Security
3. Generate an App-Specific Password
4. Use the generated password in `EMAIL_PASSWORD`

## 📁 Project Structure

```
LicensedCompetitionsTracker/
├── .env                        # Email configuration (create this)
├── .gitignore                  # Git ignore file
├── requirements.txt            # Python dependencies
├── UserData.csv               # User data for batch emails
├── README.md                  # This documentation
├── DownloadSpreadsheet.py     # Downloads competition data
├── ParseSpreadsheet.py        # Parses downloaded spreadsheets
├── PostCodeDistanceCalc.py    # Calculates distances between postcodes
├── FindCompetitions.py        # Interactive competition finder
├── EmailResults.py            # Generates and sends email reports
├── downloads/                 # Downloaded spreadsheet files
├── emails/                    # Generated HTML email files
└── venv/                      # Virtual environment (if created)
```

## 🚀 Usage

### 1. Download Competition Data

First, download the latest competition data from England Athletics:

```bash
python DownloadSpreadsheet.py
```

This will:

- Download the latest licensed competitions spreadsheet
- Save it to the `downloads/` folder with a timestamp
- Show download progress and file information

### 2. Find Competitions Near You (Interactive)

Use the interactive competition finder:

```bash
python FindCompetitions.py
```

This will:

- Prompt you for your postcode
- Ask for maximum distance in miles
- Search for competitions within that distance
- Display results with distances, dates, and venues
- Offer to save results to CSV

**Example session:**

```
Find Competitions Near You
==============================
Enter your postcode: SW1A 1AA
Enter maximum distance in miles: 25

Searching for competitions within 25.0 miles of SW1A 1AA...
Found 8 competitions within 25.0 miles:

1. London Marathon
   Distance: 5.2 miles
   Date: 2025-04-13
   Venue: Greenwich Park

2. Crystal Palace Open
   Distance: 12.8 miles
   Date: 2025-05-15
   Venue: Crystal Palace Athletics Stadium
```

### 3. Generate Email Reports for Multiple Users

#### Step 1: Set Up User Data

Create or edit `UserData.csv` with user information:

```csv
Name,Email,Postcode,MaxDistance
John Smith,john@example.com,M1 1AA,30
Jane Doe,jane@example.com,B1 1BB,25
Mike Johnson,mike@example.com,LS1 1CC,40
```

#### Step 2: Generate and Send Emails

```bash
python EmailResults.py
```

This will:

- Read user data from `UserData.csv`
- For each user, find competitions within their specified distance
- Generate beautiful HTML emails with competition details
- Save emails as HTML files in the `emails/` folder
- Optionally send emails via SMTP (if configured)

**Example output:**

```
Licensed Competitions Tracker - Email Results Generator
============================================================
📧 Email sending: ENABLED
📧 SMTP Server: smtp.gmail.com:587
📧 From: Athletics Competitions Tracker <your_email@gmail.com>

Processing 3 users...

Processing user 1/3: John Smith (M1 1AA)
  ✅ Email saved to: emails/email_john_smith_20250920_143022.html
  📧 Email sent successfully to john@example.com
  📍 Found 12 competitions within 30 miles
```

### 4. Parse and Analyze Data

To examine the downloaded spreadsheet data:

```bash
python ParseSpreadsheet.py
```

This will:

- Load the latest downloaded spreadsheet
- Display column information and data types
- Show the first few rows of data
- Save a sample to `parsed_data_sample.csv`

## 📧 Email Features

### Generated Email Content Includes:

- **📊 Statistics Dashboard**: Total competitions found, closest, furthest, and average distances
- **🏆 Competition Cards**: Individual cards for each competition with:
  - Competition name and organizing body
  - Distance from user's location
  - Date and venue information
  - License level details
- **🔍 Search Links**: Quick access to:
  - Google web search for competition details
  - Google Maps for venue directions
- **🎨 Responsive Design**: Looks great on desktop and mobile devices

### Sample Email Features:

The generated emails include:

- Professional gradient header with athletics theme
- Personalized greeting using the user's name
- Search parameters summary (postcode and max distance)
- Color-coded distance badges for each competition
- Hover effects and professional styling
- Mobile-friendly responsive design

## 🔧 Advanced Usage

### Custom Postcode Distance Calculation

You can use the distance calculator independently:

```python
from PostCodeDistanceCalc import PostcodeDistanceCalculator

calc = PostcodeDistanceCalculator("SW1A 1AA")  # Your postcode
distance = calc.calculate_distance_to_postcode("M1 1AA")  # Target postcode
print(f"Distance: {distance} miles")
```

### Custom Data Processing

```python
from ParseSpreadsheet import parse_spreadsheet_to_dataframe
from FindCompetitions import find_competitions_within_distance

# Load and process data
competitions = find_competitions_within_distance("SW1A 1AA", 50)
print(f"Found {len(competitions)} competitions")
```

## 🛠️ Configuration Options

### Environment Variables

| Variable         | Description             | Example                |
| ---------------- | ----------------------- | ---------------------- |
| `SMTP_SERVER`    | Email server hostname   | `smtp.gmail.com`       |
| `SMTP_PORT`      | Email server port       | `587`                  |
| `EMAIL_USERNAME` | Your email address      | `your_email@gmail.com` |
| `EMAIL_PASSWORD` | App password            | `your_app_password`    |
| `FROM_NAME`      | Display name for emails | `Athletics Tracker`    |
| `REPLY_TO`       | Reply-to email address  | `your_email@gmail.com` |
| `SEND_EMAILS`    | Enable/disable sending  | `true` or `false`      |

### UserData.csv Format

| Column        | Description                         | Example                 |
| ------------- | ----------------------------------- | ----------------------- |
| `Name`        | User's display name                 | `John Smith`            |
| `Email`       | User's email address                | `john@example.com`      |
| `Postcode`    | UK postcode (with or without space) | `SW1A1AA` or `SW1A 1AA` |
| `MaxDistance` | Maximum distance in miles           | `25`                    |

## 🔍 Troubleshooting

### Common Issues:

**1. "Could not find coordinates for postcode"**

- Check postcode spelling and format
- Ensure postcode is valid UK postcode
- Try with and without spaces

**2. "No spreadsheet files found"**

- Run `DownloadSpreadsheet.py` first
- Check the `downloads/` folder exists
- Verify internet connection

**3. "Email configuration not available"**

- Check `.env` file exists in project root
- Verify all required email settings are present
- Test with `SEND_EMAILS=false` first

**4. "Authentication failed" (Email)**

- Use App Password, not regular password
- Enable 2-factor authentication first
- Check SMTP server and port settings

**5. "Import errors"**

- Activate virtual environment: `source venv/bin/activate`
- Install requirements: `pip install -r requirements.txt`
- Check Python version: `python --version` (needs 3.7+)

## 📊 Data Sources

- **Competition Data**: England Athletics Licensed Competitions - https://www.englandathletics.org/?media-alias=edddfc51d3f1e36a1f78
- **Postcode Coordinates**: [postcodes.io](https://postcodes.io) (free UK postcode API)
- **Distance Calculation**: Haversine formula for great-circle distances

## 🔒 Security Notes

- The `.env` file is automatically excluded from git (via `.gitignore`)
- Never commit email passwords to version control
- Use app-specific passwords, not your main email password
- Revoke app passwords if compromised

## 🤝 Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is provided as-is for personal use. Please respect England Athletics' data usage policies when using their competition data.

## 📞 Support

For issues or questions:

1. Check the troubleshooting section above
2. Verify your setup matches the installation guide
3. Test with sample data first
4. Check that all dependencies are installed correctly

---

**Happy Athletics Tracking! 🏃‍♂️🏃‍♀️**
