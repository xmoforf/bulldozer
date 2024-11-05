# utils.py
import subprocess
import logging
import yaml
import re
import shutil
import fnmatch
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from yaspin import yaspin
from titlecase import titlecase
from logging.handlers import RotatingFileHandler
from .cache import Cache

def run_command(command, progress_description=None, track_progress=False, total_episodes=None):
    """
    Run a shell command and return the output.

    :param command: The shell command to run.
    :param progress_description: The description to display during progress.
    :param track_progress: If True, track the progress of the command.
    :param total_episodes: The total number of episodes to track progress.

    :return: The output of the command and the return code.
    """
    output = []
    episode_count = -1
    log(f"Running command: {command}", level="debug")
    with spinner(progress_description) as spin:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(process.stdout.readline, b''):
            if line:
                decoded_line = line.decode('utf-8').strip()
                output.append(decoded_line)
                if track_progress and "Download complete" in decoded_line:
                    episode_count += 1
                    spin.text = f"{progress_description} ({episode_count}/{total_episodes})"
        process.wait()
        if process.returncode == 0:
            spin.ok("✔")
        else:
            spin.fail("✖")
    return '\n'.join(output), process.returncode

@contextmanager
def spinner(text):
    """
    Create a spinner context manager.

    :param text: The text to display with the spinner.
    :return: The spinner object.
    """
    with yaspin(text=text, color="cyan") as spin:
        yield spin

def load_config():
    """
    Load the configuration settings.

    :return: The configuration settings.
    """
    global config
    base_config_file = Path("config.default.yaml")
    user_config_file = Path("config.yaml")
    if not base_config_file.exists():
        log("'config.default.yaml' not found.", "error")
        return None
    with open(base_config_file, 'r') as base_file:
        base_config = yaml.safe_load(base_file)

    if not base_config:
        log("Failed to load base config file.", "error")
        return None
    
    try:
        with open(user_config_file, 'r') as user_file:
            user_config = yaml.safe_load(user_file)
    except FileNotFoundError:
        log("'config.yaml' not found, will only use defaults.", "debug")
        user_config = {}

    config = {**base_config, **user_config}

    return config

def setup_logging(log_level, config=None):
    """
    Setup the logging configuration.

    :param log_level: The log level to set.
    :param config: The configuration settings.
    """
    config = config or {}
    logs = Path("logs")
    logs.mkdir(exist_ok=True)
    
    logfile_size_mb = config.get("logfile_size_mb", 1)
    logfile_count = config.get("logfile_count", 5)
    handler = RotatingFileHandler(
        "logs/podshare.log",
        maxBytes=logfile_size_mb * 1024 * 1024,
        backupCount=logfile_count
    )
    
    config_log_level = config.get("log_level", "WARNING").upper()
    effective_log_level = log_level if log_level else config_log_level
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(effective_log_level)
    if not root_logger.hasHandlers():
        root_logger.addHandler(handler)
    
    log(f"Log level set to {effective_log_level}", "debug")

def log(text, level="info"):
    """
    Log a message with the specified level.

    :param text: The message to log.
    :param level: The log level.
    """
    if level == "info":
        logging.info(text)
    elif level == "warning":
        logging.warning(text)
    elif level == "error":
        logging.error(text)
    elif level == "debug":
        logging.debug(text)
    else:
        raise ValueError(f"Invalid log level: {level}")
    
def announce(text, type=None):
    """
    Announce a message with a specific type.

    :param text: The message to announce.
    :param type: The type of announcement.
    """
    prepend = "  "
    if type == "critical":
        prepend = "❌"
    if type == "error":
        prepend = "❗️"
    if type == "warning":
        prepend = "⚠️"
    if type == "info":
        prepend = "ℹ️"
    if type == "celebrate":
        prepend = "🎉"
    print(f"{prepend}{text}")

def ask_yes_no(question):
    """
    Ask a yes/no question.

    :param question: The question to ask.
    :return: True if the answer is yes, False otherwise.
    """
    while True:
        response = input(f"❓{question} (y/N): ").strip().lower()
        if response == 'y':
            return True
        else:
            return False
        
def take_input(prompt):
    """
    Take input from the user.

    :param prompt: The prompt to display.
    :return: The user's input.
    """
    while True:
        response = input(f"⌨️{prompt}: ").strip()
        if response == '':
            return None
        else:
            return response
        
def get_metadata_directory(folder_path, config):
    """
    Get the path to the metadata directory.

    :param folder_path: The path to the podcast folder.
    :param config: The configuration settings.
    :return: The path to the metadata directory.
    """
    return folder_path / get_metadata_directory_name(config)
        
def get_metadata_directory_name(config):
    """
    Get the name of the metadata directory.

    :param config: The configuration settings.
    :return: The name of the metadata directory.
    """
    return config.get('metadata_directory', 'Metadata')

def special_capitalization(word, config, **kwargs):
    """
    Apply special capitalization rules to a word.

    :param word: The word to capitalize.
    :param config: The configuration settings.
    :return: The capitalized word.
    """
    patterns_uppercase = config.get('force_uppercase', [])
    patterns_titlecase = config.get('force_titlecase', [])
    patterns_skip = config.get('skip_capitalization', [])
    for pattern in patterns_uppercase:
        if re.match(pattern, word, re.IGNORECASE):
            return word.upper()
    for pattern in patterns_titlecase:
        if re.match(pattern, word, re.IGNORECASE):
            return word.title()
    for pattern in patterns_skip:
        if re.search(pattern, word, re.IGNORECASE):
            return word
    return None

def titlecase_filename(file_path, config):
    """
    Titlecase the filename with special capitalization rules.

    :param file_path: The path to the file.
    :param config: The configuration settings.
    :return: The titlecased filename.
    """
    new_stem = titlecase(file_path.stem, callback=lambda word, **kwargs: special_capitalization(word, config, **kwargs))
    return new_stem + file_path.suffix

@contextmanager
def open_file_case_insensitive(filename, folder_path, mode='r'):
        """
        Open a file in a case-insensitive manner.

        :param filename: The name of the file to open.
        :param folder_path: The path to the folder to search in.
        :param mode: The mode to open the file in.
        :return: The file object.
        """
        target_file_name = filename.lower()

        for file in folder_path.iterdir():
            if file.is_file() and file.name.lower() == target_file_name:
                f = file.open(mode)
                try:
                    yield f
                finally:
                    f.close()
                return
        log(f"No file matching '{filename}' found in '{folder_path}'", "debug")
        yield None

def archive_metadata(file_path, target_path):
    """
    Archive the metadata file to a target path.

    :param file_path: The path to the metadata file.
    :param target_path: The path to the target folder.
    :return: True if the file was archived successfully, False otherwise.
    """
    if not target_path:
        return False
    target_path = Path(target_path)
    if not target_path.exists():
        target_path.mkdir(parents=True)
    target_file_path = target_path / file_path.name
    shutil.copy(file_path, target_file_path)
    log(f"Archived metadata file to {target_file_path}", "debug")
    return True

def format_last_date(date_str, date_format_long="%B %d %Y"):
    """
    Format the last date in a long format.

    :param date_str: The date string to format.
    :param date_format_long: The long date format.
    :return: The formatted date string
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime(date_format_long)

def find_case_insensitive_files(pattern, folder_path='.'):
    """
    Find files in the podcast folder that match a pattern in a case-insensitive manner.

    :param pattern: The pattern to match against the file names.
    :param folder_path: The path to the folder to search in.
    :return: A list of file paths that match the pattern.
    """
    matches = []
    pattern = pattern.lower()
    for file in folder_path.iterdir():
        if fnmatch.fnmatch(file.name.lower(), pattern):
            matches.append(folder_path / file.name)
    return matches

def get_from_cache(key):
    """
    Get data from the cache.

    :param key: The key to get the data for.
    :return: The data.
    """
    global config
    cache = Cache(config)
    return cache.get(key)

def write_to_cache(key, data):
    """
    Write data to the cache.

    :param key: The key to write the data to.
    :param data: The data to write.
    :return: True if the data was written successfully, False otherwise.
    """
    global config
    cache = Cache(config)
    return cache.write(key, data)