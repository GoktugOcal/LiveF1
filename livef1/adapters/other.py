import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def _parse_tables_from_wikipedia(url):
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Store parsed tables with associated titles
    tables_dict = {}
    all_tables = soup.find_all('table', class_='wikitable')

    for i, table in enumerate(all_tables):
        # Try caption first
        caption = table.find('caption')
        if caption:
            title = caption.get_text(strip=True)
        else:
            # No caption: find closest previous header (h2-h6)
            prev = table.find_previous(['h2', 'h3', 'h4', 'h5', 'h6'])
            if prev:
                title = prev.get_text(strip=True).replace('[edit]', '')
            else:
                title = f'Table {i+1}'  # fallback generic title

        # Read the table with pandas
        df = pd.read_html(str(table))[0]
        tables_dict[title] = df
    
    return tables_dict

def get_table_from_wikipedia(url, table_name):
    tables_dict = _parse_tables_from_wikipedia(url)
    
    try:
        return tables_dict.get(table_name)
    except:
        return None


def parse_schedule_from_f1com(season: int) -> pd.DataFrame:
    """Parse the schedule for the given season from the official Formula 1 website.
    Args:
        season (int): The year of the season to parse.
    Returns:
        pd.DataFrame: A DataFrame containing the schedule with columns:
            - "Meeting Circuit Shortname"
            - "Meeting Offname"
            - "Session Name"
            - "Start Date"
            - "End Date"
    """

    BASE_URL = 'https://www.formula1.com'
    SEASON_URL = BASE_URL + f'/en/racing/{season}'

    """Given a race weekend URL, return a dict of session names → datetime."""
    resp = requests.get(SEASON_URL)
    soup = BeautifulSoup(resp.content, 'html.parser')

    meetings = []
    for meeting_obj in soup.find_all('a', class_='group'):

        short_name = meeting_obj.find(class_="typography-module_display-xl-bold__Gyl5W").text
        offname = meeting_obj.find(class_="typography-module_body-xs-semibold__Fyfwn").text
        meeting_url = BASE_URL + meeting_obj["href"]

        sub_resp = requests.get(meeting_url)
        sub_soup = BeautifulSoup(sub_resp.content, 'html.parser')

        ul = sub_soup.find('ul', class_="contents")
        items = [li for li in ul.find_all('li')]
        sessions = {}

        for item in items:
            session_name = item.find(class_="typography-module_display-m-bold__qgZFB").text
            times = item.find_all("time")

            day = item.find(class_="typography-module_technical-l-bold__AKrZb").text
            month = item.find(class_="typography-module_technical-s-regular__6LvKq").text
            season = 2025

            if len(times) > 1:
                start = times[0].text
                end = times[1].text
                start_date = datetime.strptime(f"{day} {month} {season} - {start}", "%d %b %Y - %H:%M")
                end_date = datetime.strptime(f"{day} {month} {season} - {end}", "%d %b %Y - %H:%M")

            else:
                start = times[0].text
                end = None
                start_date = datetime.strptime(f"{day} {month} {season} - {start}", "%d %b %Y - %H:%M")
                end_date = None
            
            sessions[session_name] = {
                "start_date" : start_date,
                "end_date" : end_date
            }
        

        meetings.append(
            {
                "short_name" : short_name,
                "offname" : offname,
                "sessions" : sessions
            }
        )
        

    row = []
    for meeting in meetings:

        meeting_shortname = meeting.get("short_name")
        meeting_offname = meeting.get("offname")
        sessions = meeting.get("sessions")
        
        for session_name, dates in sessions.items():
            row.append(
                [
                    meeting_shortname,
                    meeting_offname,
                    session_name,
                    dates["start_date"],
                    dates["end_date"]
                    ]
            )

    schedule_df = pd.DataFrame(row, columns=["Meeting Circuit Shortname", "Meeting Offname", "Session Name", "Start Date", "End Date"])
    return schedule_df