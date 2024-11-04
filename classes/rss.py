# rss.py
import requests
import re
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from titlecase import titlecase
from .utils import spinner, get_metadata_directory, log
from .utils import special_capitalization, announce

class Rss:
    def __init__(self, podcast, source_rss_file, config, censor_rss):
        """
        Initialize the Rss with the podcast, source RSS file, configuration, and censor RSS flag.

        :param podcast: The podcast object containing information about the podcast.
        :param source_rss_file: The source RSS file to download.
        :param config: The configuration settings.
        :param censor_rss: If True, the RSS feed will be censored.

        The Rss class is responsible for downloading and processing the RSS feed for the podcast.
        """
        self.podcast = podcast
        self.source_rss_file = source_rss_file
        self.config = config
        self.censor_rss = censor_rss
        self.keep_source_rss = self.config.get('keep_source_rss', False)
        self.metadata = dict()

    def get_file_path(self):
        """
        Get the path to the RSS feed file.

        :return: The path to the RSS feed file.
        """
        file_name = 'podcast.rss' if self.podcast.name == 'unknown podcast' else f'{self.podcast.name}.rss'
        return get_metadata_directory(self.podcast.folder_path, self.config) / file_name

    def extract_folder_name_from(self):
        """
        Extract the folder name from the RSS feed.

        :return: The folder name extracted from the RSS feed.
        """
        tree = ET.parse(self.get_file_path())
        root = tree.getroot()
        channel = root.find('channel')
        if channel is not None:
            title = channel.find('title')
            if title is not None:
                new_title = title.text.replace("_", " -").replace(":", " -").replace(" | Wondery+ Edition", "").replace(" | Wondery+", "")
                new_title = re.sub(r'[^\w\s-]', '', new_title)
                new_title = new_title.strip().strip('-')
                return titlecase(new_title, callback=lambda word, **kwargs: special_capitalization(word, self.config, **kwargs))
        return None 

    def get_episode_count_from(self):
        """
        Get the episode count from the RSS feed.

        :return: The episode count from the RSS feed.
        """
        tree = ET.parse(self.get_file_path())
        root = tree.getroot()
        channel = root.find('channel')
        if channel is not None:
            items = channel.findall('item')
            return len(items)
        return 0
    
    def rename(self):
        """
        Rename the RSS file to the podcast name.
        """
        old_file_path = get_metadata_directory(self.podcast.folder_path, self.config) / f'podcast.rss'
        new_file_path = get_metadata_directory(self.podcast.folder_path, self.config) / f'{self.podcast.name}.rss'
        log(f"Renaming RSS file from {old_file_path} to {new_file_path}", "debug")
        old_file_path.rename(new_file_path)

    def get_metadata(self):
        """
        Get the metadata from the RSS feed.

        :return: True if the metadata was successfully extracted, False otherwise.
        """
        if not self.get_file_path().exists():
            self.get_file()

        if not self.get_file_path().exists():
            log("RSS file could not be fetched", "error")
            return False

        with spinner("Getting metadata from feed") as spin:
            self.metadata['name'] = self.extract_folder_name_from()
            if not self.metadata['name']:
                spin.fail("✖")
                log("Failed to extract name from RSS feed", "error")
                exit(1)

            new_folder_path = self.podcast.folder_path.parent / f'{self.metadata['name']}'
            if new_folder_path.exists():
                spin.fail("✖")
                announce(f"Folder {new_folder_path} already exists - can't continue", "error")
                log(f"Folder {new_folder_path} already exists", "error")
                exit(1)
            self.podcast.folder_path.rename(new_folder_path)
            log(f"Folder renamed to {new_folder_path}", "debug")
            self.podcast.folder_path = new_folder_path
            self.podcast.name = self.metadata['name']
            self.rename()
            self.metadata['total_episodes'] = self.get_episode_count_from()
            self.check_for_premium_show()
            spin.ok("✔")

        return True

    def download_file(self):
        """
        Download the RSS feed file.
        """
        with spinner("Downloading RSS feed") as spin:
            try:
                response = requests.get(self.source_rss_file)
                response.raise_for_status()
                with self.get_file_path().open('wb') as rss_file:
                    rss_file.write(response.content)
                log(f"RSS feed downloaded to {self.get_file_path()}", "debug")
                spin.ok("✔")
            except requests.RequestException as e:
                spin.fail("✘")
                log(f"Failed to download RSS feed", "error")
                log(e, "debug")
                raise
    
    def load_local_file(self):
        """
        Load the local RSS feed file.
        """
        if self.keep_source_rss:
            shutil.copy(self.source_rss_file, self.get_file_path())
        else:
            self.source_rss_file.rename(self.get_file_path())
            self.source_rss_file = None

    def get_file(self):
        """
        Get the RSS feed file.
        """
        if not self.source_rss_file:
            return False
        
        self.get_file_path().parent.mkdir(parents=True, exist_ok=True)

        if os.path.exists(self.source_rss_file):
            self.source_rss_file = Path(self.source_rss_file).resolve()
            self.load_local_file()
        else:
            self.download_file()
        
    def delete_file(self):
        """
        Delete the RSS feed file.
        """
        if self.censor_rss:
            if self.get_file_path().exists():
                self.get_file_path().unlink()
                log(f"RSS feed deleted since censor was true: {self.get_file_path()}", "debug")

    def check_for_premium_show(self):
        """
        Check if the podcast is a premium show.

        :return: A string indicating the premium status of the podcast.
        """
        if not self.get_file_path().exists():
            log("RSS file does not exist, can't check for premium status", "warning")
            return ""
        tree = ET.parse(self.get_file_path())
        root = tree.getroot()
        channel = root.find('channel')
        if channel is not None:
            title = channel.find('title')
            if title is not None:
                for network in self.config.get('premium_networks', []):
                    if network in title.text:
                        self.censor_rss = True
                        if not self.config.get('include_premium_tag', True):
                            return ""
                        return f" ({network})"
        return ""
