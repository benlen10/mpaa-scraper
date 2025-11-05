import sqlite3
import re

DB_PATH = 'mpaa_ratings.db'

def extract_rating_from_descriptor(descriptor):
    """Extract rating letter from descriptor text like 'Rated R for...'"""
    # Pattern handles: R, PG, PG-13, NC-17, G, etc.
    # Also handles edge cases like "Rated Rated PG-13" and "PG-13 for..."

    # Try: "Rated [Rated] RATING for..."
    match = re.match(r'(?:Rated\s+)+([A-Z]+(?:-\d+)?(?:/[A-Z-]+)?)\s+for', descriptor)
    if match:
        return match.group(1)

    # Try: "RATING for..." (without "Rated" prefix)
    match = re.match(r'([A-Z]+(?:-\d+)?(?:/[A-Z-]+)?)\s+for', descriptor)
    if match:
        return match.group(1)

    return None

def check_missing_ratings():
    """Check for any entries still missing ratings"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, film_title, year, descriptors
        FROM ratings
        WHERE rating IS NULL OR rating = ''
    ''')

    rows = cursor.fetchall()
    conn.close()

    if rows:
        print(f"\n⚠️  Found {len(rows)} entries still missing ratings:")
        for row_id, title, year, descriptor in rows[:10]:  # Show first 10
            print(f"  ID {row_id}: {title} ({year})")
            print(f"    Descriptor: {descriptor[:80] if descriptor else 'None'}...")
        if len(rows) > 10:
            print(f"  ... and {len(rows) - 10} more")
    else:
        print("\n✓ All entries have ratings!")

    return len(rows)

def fix_missing_ratings():
    """Update database entries with missing ratings by extracting from descriptors"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find all entries with empty or missing rating but have descriptors
    cursor.execute('''
        SELECT id, descriptors
        FROM ratings
        WHERE (rating IS NULL OR rating = '')
        AND descriptors IS NOT NULL
        AND descriptors != ''
    ''')

    rows = cursor.fetchall()
    fixed_count = 0

    print(f"Found {len(rows)} entries with missing ratings but have descriptors")

    for row_id, descriptor in rows:
        rating = extract_rating_from_descriptor(descriptor)

        if rating:
            cursor.execute('UPDATE ratings SET rating = ? WHERE id = ?', (rating, row_id))
            fixed_count += 1
            print(f"  Fixed ID {row_id}: extracted rating '{rating}' from: {descriptor[:60]}...")

    conn.commit()
    conn.close()

    print(f"\n=== Complete ===")
    print(f"Fixed {fixed_count} out of {len(rows)} entries")

if __name__ == '__main__':
    fix_missing_ratings()
    check_missing_ratings()
