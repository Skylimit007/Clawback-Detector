from flask import Flask, request, send_file, render_template, redirect, url_for
import csv
import re
from collections import defaultdict
from datetime import datetime
import os
import sqlite3
import hashlib
import pdfplumber
import pandas as pd

app = Flask(__name__)
app.static_folder = 'static'  # Specify the static folder

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to authenticate user
def authenticate_user(username, password):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()

    hashed_password = hash_password(password)

    cur.execute('''
        SELECT * FROM users WHERE username = ? AND password = ?
    ''', (username, hashed_password))

    user = cur.fetchone()

    conn.close()

    if user:
        return True
    else:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    username = request.form['username']
    password = request.form['password']

    if authenticate_user(username, password):
        return redirect(url_for('upload_file'))
    else:
        return "Invalid credentials"

def convert_pdf_to_csv(file_path):
    output_file = 'converted.csv'
    
    with pdfplumber.open(file_path) as pdf:
        all_text = []
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                all_text.extend(table)
                
    df = pd.DataFrame(all_text)
    df.to_csv(output_file, index=False, header=False)
    
    return output_file

def highlight_rows(file_name):
    data = []
    with open(file_name, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            data.append(row)

    number_frequency = defaultdict(list)

    # Regex pattern to capture the numbers including the last three digits after ***
    pattern = re.compile(r"(\d{6}\*\*\*\d{3})")

    # Iterate through the data and extract the numbers
    for row in data:
        if "Deposit" in row[3] or "Withdrawal" in row[3]:
            match = pattern.search(row[3])
            if match:
                number = match.group(1)
                number_frequency[number].append(row)

    # Create a list to store the highlighted rows
    highlights = []

    # Check for rows with more than 1 occurrence of the same number
    for number, rows in number_frequency.items():
        if len(rows) > 1:
            highlights.extend(rows)

    return highlights

@app.route('/upload')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['POST'])
def uploader():
    if 'fileup' not in request.files:
        return "No file part"
    file = request.files['fileup']
    if file.filename == '':
        return "No selected file"
    file_path = os.path.join('/tmp', file.filename)
    file.save(file_path)

    try:
        csv_file = convert_pdf_to_csv(file_path)
        highlights = highlight_rows(csv_file)
        output_file = os.path.join('static', 'highlights.csv')
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(highlights)
        return render_template('summary.html', highlights=highlights, download_link=url_for('download_file'))
    except Exception as e:
        return str(e)

@app.route('/download')
def download_file():
    file_path = os.path.join('static', 'highlights.csv')
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
