# MPAA Film Ratings Scraper

A simple web scraper and browser for MPAA film ratings data.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the web interface
python app.py
```

Visit http://localhost:5000 to browse ratings.

## Features

- Scrapes MPAA film ratings from filmratings.com
- SQLite database for storage
- Web UI with search, filter, and sorting
- Export to CSV/JSON
- Incremental scraping (only fetches new data)

## Usage

**Scrape new data:**
```bash
python scrape.py
```

**Fix missing ratings:**
```bash
python fix_ratings.py
```

## Tech Stack

- Python 3 + Flask
- SQLite
- BeautifulSoup4 + Requests
- Vanilla JavaScript (no frameworks)

## Database Schema

- Title, Year, Rating, Rated Date, Distributor, Certificate #, Descriptors, Scrape Date
