import sqlite3

# Create table if it doesn't exist
def initialize_database():
    conn = sqlite3.connect('data/people.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS people
                  (iin TEXT PRIMARY KEY,
                   has_debt BOOLEAN,
                   health_issues BOOLEAN,
                   mentally_unstable BOOLEAN,
                   drug_use BOOLEAN,
                   alcohol_use BOOLEAN,
                   description TEXT)''')
    conn.commit()
    conn.close()

# Function to add a person to the database
def add_person_to_db(iin, data):
    conn = sqlite3.connect('data/people.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO people (iin, has_debt, health_issues, mentally_unstable, drug_use, alcohol_use, description)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (iin, data['has_debt'], data['health_issues'], data['mentally_unstable'], data['drug_use'], data['alcohol_use'], data['description']))
    conn.commit()
    conn.close()

# Function to find a person by ИИН (ID)
def find_person_by_iin(iin):
    conn = sqlite3.connect('data/people.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM people WHERE iin = ?', (iin,))
    person = cursor.fetchone()
    conn.close()
    return person  # Returns None if not found
