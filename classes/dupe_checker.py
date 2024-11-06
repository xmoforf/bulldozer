# dupe_checker.py
import requests
from .utils import announce, log, ask_yes_no

class DupeChecker:
    def __init__(self, search_name, url, api_key, warn=True):
        """
        Initialize the DupeChecker with the search name, URL, API key, and warning flag.
        
        :param search_name: The name to search for duplicates.
        :param url: The URL of the API to check for duplicates.
        :param api_key: The API key for authentication.
        :param warn: Flag to indicate if warnings should be issued.

        The DupeChecker class is responsible for checking for duplicates using the provided API.
        """
        self.search_name = search_name
        self.url = url
        self.api_key = api_key
        self.warn = warn

    def check_duplicates(self, report_no_dupes=False):
        """
        Check for duplicates using the provided API.
        
        :param report_no_dupes: Flag to indicate if a report should be generated when no duplicates are found.
        :return: True if duplicates were found or no duplicates were found and the user wants to continue, False otherwise.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        params = {
            "name": self.search_name,
        }

        ask_user = False

        try:
            response = requests.get(self.url, headers=headers, params=params)
            response.raise_for_status()
            torrents = response.json()
            if torrents['data']:
                announce("Possible duplicates found:", "warning")
                ask_user = True
                for torrent in torrents['data']:
                    announce(f"- {torrent['attributes']['name']}: {torrent['attributes']['details_link']}")
            elif report_no_dupes:
                announce(f'Nothing found for "{self.search_name}"', 'info')
                
        except requests.exceptions.RequestException as e:
            announce(f"An error occurred while checking for duplicates", "error")
            log(e, "debug")
            ask_user = True
        
        if self.warn and ask_user:
            if not ask_yes_no("Do you want to continue"):
                return False

        return True
