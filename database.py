import os
import psycopg2

# Получение соединения с базой данных
def get_database_connection():
    database_url = os.getenv("DATABASE_URL")  
    return psycopg2.connect(database_url, sslmode='require')

def initialize_database():
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS people (
            iin TEXT PRIMARY KEY,
            has_debt BOOLEAN,
            health_issues BOOLEAN,
            mentally_unstable BOOLEAN,
            drug_use BOOLEAN,
            alcohol_use BOOLEAN,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_person_to_db(iin, data):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO people (iin, has_debt, health_issues, mentally_unstable, drug_use, alcohol_use, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (iin, data['has_debt'], data['health_issues'], data['mentally_unstable'], data['drug_use'], data['alcohol_use'], data['description']))
    conn.commit()
    conn.close()

def find_person_by_iin(iin):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM people WHERE iin = %s', (iin,))
    person = cursor.fetchone()
    conn.close()
    return person
