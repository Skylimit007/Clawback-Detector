import sqlite3
import hashlib

def initialize_database():
    # Connect to the database (or create it if it doesn't exist)
    conn = sqlite3.connect('users.db')

    # Create a cursor object
    cur = conn.cursor()

    # Create the users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()

    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cur.execute('''
            INSERT INTO users (username, password)
            VALUES (?, ?)
        ''', (username, hashed_password))
        conn.commit()
        print("User registered successfully!")
    except sqlite3.IntegrityError:
        print("Username already exists.")
    finally:
        conn.close()

if __name__ == '__main__':
    initialize_database()
    username = input("Enter username: ")
    password = input("Enter password: ")
    register_user(username, password)
