import os
from flask import Flask, render_template, request, redirect, session
from dotenv import load_dotenv

load_dotenv() # load environment variables from .env file

app = Flask(
    __name__,
    template_folder=os.environ.get("TEMPLATE_FOLDER"),
)
app.secret_key = os.environ.get("SECRET_KEY")

# import user dataset from CSV file
import csv
users = {}
with open('users.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        users[row['username']] = {'password': row['password']}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and password == users[username]['password']:
            session['username'] = username
            return redirect('/')
        else:
            return render_template('login.html', error='Invalid username or password.')
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
