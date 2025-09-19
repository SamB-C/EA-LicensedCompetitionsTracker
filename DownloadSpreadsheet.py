import requests
import os
from pathlib import Path
from urllib.parse import urlparse
import time
from datetime import datetime


def download_spreadsheet(url, download_folder="downloads"):
    """
    Download a spreadsheet from the given URL.

    Args:
        url (str): The URL to download the spreadsheet from
        download_folder (str): Folder to save the downloaded file

    Returns:
        str: Path to the downloaded file, or None if download failed
    """
    try:
        # Create download folder if it doesn't exist
        Path(download_folder).mkdir(exist_ok=True)

        # Set up headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        print(f"Downloading from: {url}")

        # Make the request
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        # Determine filename from Content-Disposition header or URL
        filename = None
        if 'Content-Disposition' in response.headers:
            content_disposition = response.headers['Content-Disposition']
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')

        # If no filename from headers, create one based on content type or use generic name
        if not filename:
            content_type = response.headers.get('Content-Type', '').lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if 'excel' in content_type or 'spreadsheet' in content_type:
                if 'openxmlformats' in content_type:
                    filename = f"england_athletics_competitions_{timestamp}.xlsx"
                else:
                    filename = f"england_athletics_competitions_{timestamp}.xls"
            elif 'csv' in content_type:
                filename = f"england_athletics_competitions_{timestamp}.csv"
            else:
                filename = f"england_athletics_competitions_{timestamp}.xlsx"

        # Full path for the downloaded file
        file_path = Path(download_folder) / filename

        # Download the file
        print(f"Saving to: {file_path}")
        total_size = int(response.headers.get('Content-Length', 0))
        downloaded_size = 0

        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)

                    # Show progress if we know the total size
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        print(f"\rProgress: {progress:.1f}%",
                              end='', flush=True)

        print(f"\nDownload completed successfully!")
        print(f"File saved to: {file_path}")
        print(f"File size: {downloaded_size:,} bytes")

        return str(file_path)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def main():
    """Main function to download the England Athletics competitions spreadsheet."""
    url = "https://www.englandathletics.org/?media-alias=edddfc51d3f1e36a1f78"

    print("England Athletics Licensed Competitions Tracker")
    print("=" * 50)

    downloaded_file = download_spreadsheet(url)

    if downloaded_file:
        print(f"\nSpreadsheet downloaded successfully to: {downloaded_file}")

        # Check file size and provide additional info
        file_size = os.path.getsize(downloaded_file)
        if file_size > 0:
            print(f"File size: {file_size:,} bytes")
            print(
                "\nYou can now open this file in Excel, Google Sheets, or any spreadsheet application.")
        else:
            print("Warning: Downloaded file appears to be empty.")
    else:
        print("\nFailed to download the spreadsheet. Please check the URL and try again.")


if __name__ == "__main__":
    main()
