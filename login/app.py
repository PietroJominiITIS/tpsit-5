from flask import Flask, render_template, redirect, request
import sqlite3
import hashlib

app = Flask(__name__)


def verify_login(username, password):
    digest = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect('static/users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username FROM users
        WHERE password=? AND username=?
    ''', (digest, username, ))

    ok = len(cursor.fetchall()) > 0
    cursor.close()

    return ok


def register_user(username, password):
    if (verify_login(username, password)):
        return

    digest = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect('static/users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, password)
        VALUES (?,?)
    ''', (username, digest, ))

    conn.commit()
    cursor.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/login/submit', methods=['POST'])
def login_submit():
    if verify_login(request.form['username'], request.form['password']):
        return redirect('/dashboard')
    return redirect('/login_error')


@app.route('/dashboard')
def dashboard():
    return 'dashboard'


@app.route('/login_error')
def login_error():
    return 'login error'


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/register/submit', methods=['POST'])
def register_submit():
    register_user(request.form['username'], request.form['password'])
    return redirect('/login')


if __name__ == "__main__":
    app.run('127.0.0.1', 5000)
