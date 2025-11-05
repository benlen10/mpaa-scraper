import sqlite3
import csv
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import io

app = Flask(__name__)
DB_PATH = 'mpaa_ratings.db'

def init_db():
    """Initialize the SQLite database with schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cert_number TEXT,
            film_title TEXT NOT NULL,
            year INTEGER,
            rating TEXT,
            descriptors TEXT,
            alternate_titles TEXT,
            other_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON ratings(year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rating ON ratings(rating)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON ratings(film_title)')

    conn.commit()
    conn.close()

def import_csv_data():
    """Import data from CSV file to SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute('SELECT COUNT(*) FROM ratings')
    if cursor.fetchone()[0] > 0:
        print("Database already contains data. Skipping import.")
        conn.close()
        return

    csv_path = Path('output/mpaa_db.csv')
    if not csv_path.exists():
        print("CSV file not found. Skipping import.")
        conn.close()
        return

    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            if len(row) >= 7:
                cursor.execute('''
                    INSERT INTO ratings (cert_number, film_title, year, rating, descriptors, alternate_titles, other_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
                count += 1

    conn.commit()
    print(f"Imported {count} records from CSV")
    conn.close()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/ratings')
def get_ratings():
    """API endpoint to get ratings with filtering and pagination"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get query parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('search', '')
    year = request.args.get('year', '')
    rating = request.args.get('rating', '')

    # Build query
    query = 'SELECT * FROM ratings WHERE 1=1'
    params = []

    if search:
        query += ' AND film_title LIKE ?'
        params.append(f'%{search}%')

    if year:
        query += ' AND year = ?'
        params.append(year)

    if rating:
        query += ' AND rating = ?'
        params.append(rating)

    # Get total count
    count_query = query.replace('SELECT *', 'SELECT COUNT(*)')
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # Add pagination
    query += ' ORDER BY year DESC, film_title LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])

    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = [dict(row) for row in rows]

    conn.close()

    return jsonify({
        'data': results,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

@app.route('/api/export')
def export_csv():
    """Export filtered data to CSV"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get query parameters (same as get_ratings)
    search = request.args.get('search', '')
    year = request.args.get('year', '')
    rating = request.args.get('rating', '')

    # Build query (without pagination)
    query = 'SELECT * FROM ratings WHERE 1=1'
    params = []

    if search:
        query += ' AND film_title LIKE ?'
        params.append(f'%{search}%')

    if year:
        query += ' AND year = ?'
        params.append(year)

    if rating:
        query += ' AND rating = ?'
        params.append(rating)

    query += ' ORDER BY year DESC, film_title'

    cursor.execute(query, params)
    rows = cursor.fetchall()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['cert_number', 'film_title', 'year', 'rating', 'descriptors', 'alternate_titles', 'other_notes'])

    for row in rows:
        writer.writerow([row['cert_number'], row['film_title'], row['year'], row['rating'],
                        row['descriptors'], row['alternate_titles'], row['other_notes']])

    conn.close()

    # Convert to bytes for sending
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='mpaa_ratings_export.csv'
    )

@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM ratings')
    total = cursor.fetchone()[0]

    cursor.execute('SELECT DISTINCT year FROM ratings ORDER BY year')
    years = [row[0] for row in cursor.fetchall()]

    cursor.execute('SELECT DISTINCT rating FROM ratings WHERE rating != "" ORDER BY rating')
    ratings = [row[0] for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'total': total,
        'years': years,
        'ratings': ratings
    })

if __name__ == '__main__':
    init_db()
    import_csv_data()
    app.run(debug=True, port=5000)
