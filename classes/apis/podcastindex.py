# podcastindex.py
import requests
import json
import hashlib
import time
from ..utils import spinner, log, announce, ask_yes_no, get_from_cache, write_to_cache

class Podcastindex:
    def __init__(self, key, secret, url):
        self.key = key
        self.secret = secret
        self.url = url
    
    def query_api(self, name, key):
        """
        Query the Podcastindex API for a podcast by name.

        :param name: The name of the podcast to search for.
        :param key: The key to use for the cache.
        :return: The data from the API.
        """
        with spinner(f"Searching for podcast {name} on Podcastindex") as spin:
            url = f"{self.url}{name}"

            epoch_time = int(time.time())
            data_to_hash = self.key + self.secret + str(epoch_time)
            sha_1 = hashlib.sha1(data_to_hash.encode()).hexdigest()

            headers = {
                'X-Auth-Date': str(epoch_time),
                'X-Auth-Key': self.key,
                'Authorization': sha_1,
                'User-Agent': 'postcasting-index-python-cli'
            }

            response = requests.post(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
            else:
                log(f"Podcastindex query failed with status code {response.status_code}", "error")
                log(response.text, "debug")
                spin.fail('✖')
                return
            write_to_cache(key, json.dumps(data, indent=4))
            spin.ok('✔')
        return data

    def find_podcast(self, name):
        """
        Find a podcast on Podchaser by name.

        :param name: The name of the podcast to search for.
        :return: The podcast object.
        """
        key = f"podcastindex-search-{name.lower().replace(' ', '_')}.json"
        data = get_from_cache(key)
        if data:
            log(f"Found cached data for '{name}' in {key}", "debug")
            data = json.loads(data)
        if not data:
            log(f"No cached data found for '{name}' - quering Podcastindex", "debug")
            data = self.query_api(name, key)
        
        if not data:
            return None

        podcasts = data.get('feeds', [])

        announce(f"Found {len(podcasts)} podcasts matching '{name}' at Podcastindex", "info")
        for podcast in podcasts:
            log(podcast, "debug")
            title = podcast.get('title')
            id = podcast.get('id')

            if ask_yes_no(f"Continue with {title} (https://podcastindex.org/podcast/{id})"):
                return podcast
            
        return None

            
            

