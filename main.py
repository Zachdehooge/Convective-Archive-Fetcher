import io
import os

import requests
from datetime import datetime, timedelta

from dotenv import load_dotenv
from tabulate import tabulate
from dateutil import parser
import pytz
from collections import Counter

load_dotenv()

authkey = os.getenv("APIKEY")

def fetch_json_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


def parse_utc_date(utc_date_str):
    """
    Parse UTC date string to datetime object with UTC timezone
    """
    # Parse the date and ensure it's UTC
    parsed_date = datetime.fromisoformat(utc_date_str.replace('Z', '+00:00'))
    return parsed_date.replace(tzinfo=pytz.UTC)


def format_utc_date(utc_date_str):
    """
    Convert UTC ISO format date to a more readable format in local time
    """
    # Parse the date in UTC
    utc_date = parse_utc_date(utc_date_str)

    # Convert to local time
    local_tz = datetime.now(pytz.UTC).astimezone().tzinfo
    local_date = utc_date.astimezone(local_tz)

    return local_date.strftime("%B %d, %Y at %I:%M %p %Z")


def get_date_input(prompt):
    """
    Get a date input from the user with error handling
    """
    while True:
        try:
            date_input = input(prompt)

            # Allow skipping the input
            if not date_input:
                return None

            # Parse the date and make it timezone-aware in UTC
            parsed_date = parser.parse(date_input)
            return parsed_date.replace(tzinfo=pytz.UTC)
        except ValueError:
            print("Invalid date format. Please try again or press Enter to skip.")


def filter_outlooks_by_time_range(outlooks, start_date=None, end_date=None, threshold=None):
    """
    Filter outlooks based on time range and optional threshold
    """
    filtered_outlooks = []

    for outlook in outlooks:
        # Parse the UTC issue date (already timezone-aware)
        issue_date = parse_utc_date(outlook['utc_issue'])

        # Check date range
        date_in_range = True
        if start_date:
            date_in_range = date_in_range and issue_date >= start_date
        if end_date:
            date_in_range = date_in_range and issue_date <= end_date

        # Check threshold if specified
        threshold_match = not threshold or outlook['threshold'] == threshold

        # Add to filtered list if both conditions are met
        if date_in_range and threshold_match:
            filtered_outlooks.append(outlook)

    return filtered_outlooks


if __name__ == "__main__":
    # URL from the provided link
    print("Enter a location\n")
    city = input("Enter City: ")
    state = input("Enter State: ")

    base_url = "https://geocode.xyz"
    params = {
        "locate": (city + " " + state),
        "region": "US",
        "json": "1"
    }

    req_url = f"{base_url}/?{requests.utils.unquote(requests.compat.urlencode(params))}"
    try:
        resp = requests.get(req_url + f"&auth={authkey}")
        resp.raise_for_status()
    except requests.RequestException as err:
        print("Error:", err)
        exit()

    geocode_data = resp.json()

    url = f"https://mesonet.agron.iastate.edu/json/spcoutlook.py?lon={geocode_data['longt']}&lat={geocode_data['latt']}&last=0&day=1&cat=categorical"

    # Fetch the data
    json_data = fetch_json_data(url)

    if json_data:
        # Get user input for date range
        print("Enter date range for filtering (leave blank to skip)")
        start_date = get_date_input("Enter start date (e.g., March 1, 2024): ")
        end_date = get_date_input("Enter end date (e.g., May 1, 2024): ")

        # Optional threshold filter
        threshold = input("Enter threshold filter (MDT/MRGL, or press Enter to skip): ").strip() or None

        # Filter outlooks based on user input
        filtered_outlooks = filter_outlooks_by_time_range(
            json_data['outlooks'],
            start_date=start_date,
            end_date=end_date,
            threshold=threshold
        )

        # Prepare data for display
        display_data = [
            [
                outlook['threshold'],
                outlook['category'],
                format_utc_date(outlook['utc_issue']),
                format_utc_date(outlook['utc_expire']),
                format_utc_date(outlook['utc_product_issue'])
            ]
            for outlook in filtered_outlooks
        ]

        # Print results
        if display_data:

            print("\nFiltered Outlooks:")
            print(tabulate(
                display_data,
                headers=['Threshold', 'Category', 'Local Issue Date', 'Local Expire Date', 'Local Product Issue Date'],
                tablefmt='fancy_grid'
            ))

            # Count thresholds
            threshold_counts = Counter(outlook['threshold'] for outlook in filtered_outlooks)

            # Print threshold summary
            print("\nThreshold Summary:")
            for threshold, count in threshold_counts.items():
                print(f"{threshold}: {count}")

            # Total count
            print(f"\nTotal Outlooks: {len(filtered_outlooks)}\n\n")

            # Write results to a file
            filename = f"{city}_{state}_outlooks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    # Write header
                    f.write(f"Storm Outlook Report for {city}, {state}\n")
                    f.write(f"Dates: {start_date} through {end_date}\n")
                    f.write(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")

                    # Write tabulated data
                    f.write(tabulate(
                        display_data,
                        headers=['Threshold', 'Category', 'Local Issue Date', 'Local Expire Date',
                                 'Local Product Issue Date'],
                        tablefmt='fancy_grid'
                    ))

                    # Write threshold summary
                    f.write("\n\nThreshold Summary:\n")
                    for threshold, count in threshold_counts.items():
                        f.write(f"{threshold}: {count}\n")

                    # Write total count
                    f.write(f"\nTotal Outlooks: {len(filtered_outlooks)}\n")

                print(f"Report saved to {filename}")
            except Exception as e:
                print(f"Error writing to file: {e}")
                # Fallback to a simpler format if needed
                try:
                    simple_filename = f"{city}_{state}_report_simple.txt"
                    with open(simple_filename, 'w', encoding='utf-8') as f:
                        # Write simpler content without fancy formatting
                        f.write(f"Storm Outlook Report for {city}, {state}\n\n")
                        for row in display_data:
                            f.write(f"Threshold: {row[0]}, Category: {row[1]}, Issue: {row[2]}, Expire: {row[3]}\n")
                    print(f"Simplified report saved to {simple_filename}")
                except Exception as e2:
                    print(f"Could not write to file at all: {e2}")
        else:
            print("No outlooks found in the specified date range.")