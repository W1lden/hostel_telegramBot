# database.py

import sqlite3

# Create table if it doesn't exist
def initialize_database():
    conn = sqlite3.connect('data/people.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS people
                      (iin TEXT PRIMARY KEY,
                       is_criminal BOOLEAN,
                       is_man BOOLEAN,
                       is_child BOOLEAN,
                       is_student BOOLEAN,
                       description TEXT)''')
    conn.commit()
    conn.close()

# Function to add a person to the database
def add_person_to_db(iin, data):
    conn = sqlite3.connect('data/people.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO people (iin, is_criminal, is_man, is_child, is_student, description)
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (iin, data['is_criminal'], data['is_man'], data['is_child'], data['is_student'], data['description']))
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
