import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep
import html

DB_PATH = 'mpaa_ratings.db'
BASE_URL = 'https://www.filmratings.com/search-results/'

def get_max_year_in_db():
    """Get the most recent year in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(year) FROM ratings')
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else datetime.now().year

def film_exists(conn, cert_number):
    """Check if a film with this certificate number already exists"""
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM ratings WHERE cert_number = ?', (cert_number,))
    return cursor.fetchone()[0] > 0

def insert_film(conn, film_data):
    """Insert a new film into the database"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ratings (cert_number, film_title, year, rating, descriptors, alternate_titles, other_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', film_data)
    conn.commit()

def parse_film_item(item):
    """Extract film data from an HTML item div"""
    try:
        # Title
        title_elem = item.find('div', class_='item-title')
        title = html.unescape(title_elem.text.strip()) if title_elem else ''

        # Studio/Distributor
        studio_elem = item.find('div', class_='studio')
        distributor = studio_elem.text.strip() if studio_elem else ''

        # Year
        year_elem = item.find('div', class_='year')
        year = year_elem.text.strip() if year_elem else ''

        # Rating (from image alt)
        rating_img = item.find('img', class_='')
        rating = rating_img.get('alt', '') if rating_img else ''

        # Extract all body items
        body_items = item.find_all('div', class_='item-body-item')

        cert_number = ''
        descriptors = ''
        alternate_titles = ''
        other_notes = ''

        for body_item in body_items:
            label = body_item.find('span', class_='label')
            text = body_item.find('span', class_='text')

            if label and text:
                label_text = label.text.strip().lower()
                value = text.text.strip()

                if 'certificate' in label_text:
                    cert_number = value
                elif 'reason' in label_text:
                    descriptors = value
                elif 'alternate' in label_text:
                    alternate_titles = value
                elif 'other' in label_text:
                    other_notes = value

        return (cert_number, title, year, rating, descriptors, alternate_titles, other_notes)

    except Exception as e:
        print(f"Error parsing film item: {e}")
        return None

def scrape_year(year):
    """Scrape all films for a given year"""
    conn = sqlite3.connect(DB_PATH)
    new_count = 0
    skipped_count = 0
    page = 1

    print(f"\nScraping year {year}...")

    while True:
        # Construct URL with pagination
        url = f"{BASE_URL}?my={year}&pn={page}"

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all film items
            items = soup.find_all('div', class_='item grey')

            if not items:
                print(f"  No more results on page {page}")
                break

            print(f"  Processing page {page} ({len(items)} films)...")

            for item in items:
                film_data = parse_film_item(item)

                if film_data and film_data[0]:  # Has cert number
                    cert_number, title, year, rating, descriptors = film_data[0], film_data[1], film_data[2], film_data[3], film_data[4]

                    if film_exists(conn, cert_number):
                        skipped_count += 1
                        print(f"    ⊘ SKIPPED: {title}")
                        print(f"      Cert: {cert_number} | Rating: {rating}")
                        print(f"      {descriptors}")
                    else:
                        insert_film(conn, film_data)
                        new_count += 1
                        print(f"    ✓ ADDED: {title}")
                        print(f"      Cert: {cert_number} | Rating: {rating}")
                        print(f"      {descriptors}")

            page += 1
            sleep(1)  # Be respectful to the server

        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break

    conn.close()
    return new_count, skipped_count

def main():
    """Main scraper function"""
    start_year = get_max_year_in_db()
    current_year = datetime.now().year

    print(f"=== MPAA Ratings Scraper ===")
    print(f"Scraping years {start_year} to {current_year}")

    total_new = 0
    total_skipped = 0

    for year in range(start_year, current_year + 1):
        new, skipped = scrape_year(year)
        total_new += new
        total_skipped += skipped

    print(f"\n=== Scrape Complete ===")
    print(f"New films added: {total_new}")
    print(f"Existing films skipped: {total_skipped}")

if __name__ == '__main__':
    main()
