# cache.py
from pathlib import Path
from datetime import datetime

class Cache:
    def __init__(self, config):
        self.config = config
        self.cache_hours = self.config.get('cache_hours', 24)
        self.cache_directory = self.config.get('cache_directory', None)
        if self.cache_directory:
            self.cache_directory = Path(self.cache_directory)
            self.check_cache_directory()

    def check_cache_directory(self):
        if not self.cache_directory:
            return False
        if not self.cache_directory.exists():
            self.cache_directory.mkdir(parents=True)
        return True
    
    def get_cache_file(self, key):
        if not self.cache_directory:
            return None
        return self.cache_directory / key
    
    def is_cache_valid(self, key):
        cache_file = self.get_cache_file(key)
        if not cache_file:
            return False
        if not cache_file.exists():
            return False
        if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).total_seconds() > self.cache_hours * 3600:
            return False
        return True
    
    def read_cache(self, key):
        cache_file = self.get_cache_file(key)
        if not cache_file:
            return None
        with cache_file.open('r') as f:
            return f.read()
        
    def get(self, key):
        if not self.is_cache_valid(key):
            return None
        return self.read_cache(key)
        
    def write(self, key, data):
        cache_file = self.get_cache_file(key)
        if not cache_file:
            return False
        with cache_file.open('w') as f:
            f.write(data)
        return True
    
    def clear_cache(self):
        if not self.cache_directory:
            return False
        for file in self.cache_directory.iterdir():
            file.unlink()
        return True
    
    def clear_cache_file(self, key):
        cache_file = self.get_cache_file(key)
        if not cache_file:
            return False
        if cache_file.exists():
            cache_file.unlink()
        return True
    