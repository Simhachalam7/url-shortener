from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)

# Initialize the database
def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS urls 
                    (id INTEGER PRIMARY KEY, long_url TEXT, short_code TEXT, name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, expiration_time INTEGER)''')
    conn.close()

# Generate a random short URL code
def generate_short_code():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(6))

# Get the last 5 shortened URLs
def get_last_5_links():
    conn = sqlite3.connect('database.db')
    cursor = conn.execute('SELECT long_url, short_code, name FROM urls ORDER BY id DESC LIMIT 5')
    links = [{'long_url': row[0], 'short_code': row[1], 'name': row[2]} for row in cursor.fetchall()]
    conn.close()
    return links

# Get all shortened URLs
def get_all_links():
    conn = sqlite3.connect('database.db')
    cursor = conn.execute('SELECT long_url, short_code, name FROM urls')
    links = [{'long_url': row[0], 'short_code': row[1], 'name': row[2]} for row in cursor.fetchall()]
    conn.close()
    return links

# Delete a shortened URL by short code
def delete_url(short_code):
    conn = sqlite3.connect('database.db')
    conn.execute('DELETE FROM urls WHERE short_code = ?', (short_code,))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    last_links = get_last_5_links()  # Fetch last 5 shortened URLs
    return render_template('index.html', last_links=last_links)

@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form['url']
    name = request.form['name']  # Get the name (optional)
    expiry = request.form['expiry']
    short_code = generate_short_code()

    # Calculate the expiration time based on user input
    if expiry == '7':
        expiration_time = 7
    elif expiry == '30':
        expiration_time = 30
    elif expiry == '45':
        expiration_time = 45
    else:
        expiration_time = None  # No expiration for 'never'

    # Save the URL mapping to the database
    conn = sqlite3.connect('database.db')
    conn.execute('INSERT INTO urls (long_url, short_code, name, expiration_time) VALUES (?, ?, ?, ?)', (long_url, short_code, name, expiration_time))
    conn.commit()
    conn.close()

    short_url = request.host_url + short_code
    last_links = get_last_5_links()
    return render_template('index.html', short_url=short_url, last_links=last_links)

# Route to handle redirection and expiration check
@app.route('/<short_code>')
def redirect_to_url(short_code):
    conn = sqlite3.connect('database.db')
    cursor = conn.execute('SELECT id, long_url, created_at, expiration_time FROM urls WHERE short_code = ?', (short_code,))
    result = cursor.fetchone()

    if result:
        url_id, long_url, created_at, expiration_time = result
        created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')

        # Check if URL is expired
        if expiration_time:
            expiration_date = created_at + timedelta(days=expiration_time)
            if datetime.now() > expiration_date:
                # Delete expired URL from the database
                conn.execute('DELETE FROM urls WHERE id = ?', (url_id,))
                conn.commit()
                conn.close()
                return '<h1>This URL has expired and was deleted.</h1>', 404

        conn.close()
        return redirect(long_url)
    else:
        conn.close()
        return '<h1>URL not found</h1>', 404

# Route to delete a URL
@app.route('/delete/<short_code>', methods=['POST'])
def delete_link(short_code):
    delete_url(short_code)  # Delete the URL with the given short code
    return redirect(url_for('index'))

# Route to view all shortened URLs
@app.route('/all-links')
def view_all_links():
    all_links = get_all_links()
    return render_template('all_links.html', all_links=all_links)


if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True, port=5001)
