from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database setup
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS expense (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user (id))''')
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        # Use 'pbkdf2:sha256' for password hashing
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO user (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.')
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose a different one.')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM user WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Please try again.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    conn = get_db_connection()
    expenses = conn.execute("SELECT * FROM expense WHERE user_id = ?", (session['user_id'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', expenses=expenses)

@app.route('/manage_expenses', methods=['GET', 'POST'])
def manage_expenses():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        conn = get_db_connection()
        conn.execute("INSERT INTO expense (user_id, description, amount, category) VALUES (?, ?, ?, ?)", 
                     (session['user_id'], description, amount, category))
        conn.commit()
        conn.close()
        flash('Expense added successfully.')
        return redirect(url_for('dashboard'))
    return render_template('manage_expenses.html')

@app.route('/update_expense/<int:id>', methods=['GET', 'POST'])
def update_expense(id):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    expense = conn.execute("SELECT * FROM expense WHERE id = ? AND user_id = ?", (id, session['user_id'])).fetchone()
    
    # Check if the expense exists and belongs to the logged-in user
    if not expense:
        flash('Expense not found or you do not have permission to edit this expense.')
        conn.close()
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Update the expense details in the database
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        conn.execute("UPDATE expense SET description = ?, amount = ?, category = ? WHERE id = ?", 
                     (description, amount, category, id))
        conn.commit()
        conn.close()
        flash('Expense updated successfully.')
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('update_expense.html', expense=expense)

@app.route('/delete_expense/<int:id>')
def delete_expense(id):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    conn = get_db_connection()
    conn.execute("DELETE FROM expense WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Expense deleted successfully.')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)