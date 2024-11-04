# Bulldozer

Bulldozer is a script designed to automate the process of downloading, organizing, analyzing, and creating torrents for podcasts. It's highly customizable, as pretty much everything you might be interested in changing is defined in the configuration file.

## Features

- Download podcast episodes using RSS feeds.
- Check for duplicate episodes using an external API.
- Organize and analyze downloaded files.
- Generate reports based on the downloaded content.
- Automatic RSS censoring for matching premium sources.
- Create torrent files for sharing podcast episodes.

## Requirements

- Python 3.x
- Required Python packages (listed in `requirements.txt`)
- mktorrent
- podcast-dl 10.3.1+

## Installation

1. Clone the repository:
    ```sh
    git clone git@github.com:lewler/bulldozer.git
    cd bulldozer
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Install additional dependencies:
    ```sh
    sudo apt-get install libwebp-dev libavif-dev
    ```

4. Copy the example configuration file and modify it as needed:
    ```sh
    cp config.example.yaml config.yaml
    ```

## Configuration

Edit the `config.yaml` file to set up your preferences and API keys. The configuration file includes pretty much all settings that are needed to customize the behavior of the script. The settings most users need to change are at the top of the configuration file. The file has comments, and it's hopefully easy enough to understand what everything does.

## Usage

### Command Line Interface

Run the script using the command line interface:

```sh
python bulldozer <input>
```

`<input>`: RSS feed URL, directory path, local RSS file path, or name to dupecheck.

### Options
- `--censor-rss`: Make sure the RSS feed is censored.
- `--check-files`: Only check the files.
- `--dupecheck`: Search the API for <input>.
- `--make-torrent`: Only create a torrent file.
- `--log-level`: Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).

## Project Structure

- bulldozer: Main script
- classes/: Contains various classes used in the project.
  - dupe_checker.py: Checks for duplicates.
  - file_analyzer.py: Analyzes downloaded files.
  - file_organizer.py: Organizes downloaded files.
  - podcast_image.py: Handles podcast image processing.
  - podcast_metadata.py: Manages podcast metadata.
  - podcast.py: Represents a podcast and its metadata.
  - report_template.py: Templates for generating reports.
  - report.py: Generates reports based on downloaded content.
  - rss.py: Handles RSS feed operations.
  - torrent_creator.py: Creates torrent files.
  - utils.py: Utility functions.
- logs/: Contains log files.
- config.example.yaml: Example configuration file.
- requirements.txt: List of required Python packages.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes.

## Acknowledgements

- [Jinja2](https://pypi.org/project/Jinja2/) for templating.
- [PyYAML](https://pypi.org/project/PyYAML/) for YAML parsing.
- [Pillow](https://pypi.org/project/pillow/) for image processing.
- [yaspin](https://pypi.org/project/yaspin/) for terminal spinners.
- [mutagen](https://pypi.org/project/mutagen/) for audio metadata handling.
- [titlecase](https://pypi.org/project/titlecase/) for title casing.
