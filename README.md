# Quicket Event Scraper

A Python web scraper that extracts event information from Quicket's events page and saves it to a CSV file.

## Features

- Scrapes event information from Quicket's events page (https://www.quicket.co.za/events/)
- Extracts event title, location, date, and time
- Uses BeautifulSoup for HTML parsing and data extraction
- Implements rate limiting to prevent overloading the website
- Includes retry logic for failed page loads
- Handles pagination and maintains page position on reload
- Scrapes up to 10 pages of events
- Saves data to a CSV file

## Requirements

- Python 3.8+
- Chrome browser installed

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/quicket-scraper.git
   cd quicket-scraper
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Run the scraper with the following command:

```
python quicket_scraper.py
```

The script will:
1. Launch a headless Chrome browser
2. Navigate to Quicket's events page
3. Scrape event information from up to 10 pages
4. Save the data to a CSV file named `quicket_events.csv`

### Command-line Interface

For more control over the scraping process, use the command-line interface:

```
python run_scraper.py [options]
```

Available options:

- `--pages PAGES`: Maximum number of pages to scrape (default: 10)
- `--output OUTPUT`: Output CSV file name (default: quicket_events.csv)
- `--verbose`: Enable verbose logging
- `--no-headless`: Run browser in visible mode (default: headless)


Examples:

```
# Scrape 5 pages and save to custom.csv
python run_scraper.py --pages 5 --output custom.csv

# Run in visible mode with verbose logging
python run_scraper.py --no-headless --verbose

# Increase retry attempts for unstable connections
python run_scraper.py --retries 5
```

## Output

The script generates a CSV file with the following columns:
- title: The title of the event
- location: The location where the event will take place
- date: The date of the event (format: "Friday, March 14, 2025")
- time: The time of the event (format: "18:00")

## Error Handling

The script includes error handling for:
- Invalid URLs
- Missing content
- Network issues
- Pagination errors
- Cookie consent dialogs

## Rate Limiting

To prevent overloading the website, the script implements a random delay between 1-3 seconds between page requests.

## Implementation Details

- Uses Selenium to navigate the website and handle JavaScript-rendered content
- Uses BeautifulSoup for HTML parsing and data extraction
- Implements retry logic to handle temporary failures
- Maintains page position on reload to continue scraping from where it left off
- Handles cookie consent dialogs automatically

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
