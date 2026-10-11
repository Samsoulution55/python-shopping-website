from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_devstore_key_change_in_production'

DATABASE = 'store.db'

if os.path.exists(DATABASE):
    try:
        os.remove(DATABASE)
    except OSError:
        pass

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image_url TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        conn.execute("DELETE FROM products")
        
        default_products = [
            ("Professional Developer Keyboard", "Mechanical keys for fast typing setup.", 89.99, "⌨️"),
            ("Ergonomic Developer Mouse", "Designed to reduce long-term wrist pain.", 59.50, "🖱️"),
            ("Dual 4K Programming Monitor", "Built for crisp layout viewports.", 299.99, "🖥️")
        ]
        
        conn.executemany("INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)", default_products)
        conn.commit()

init_db()

@app.route('/')
def storefront():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    search_query = request.args.get('search', '').strip()
    db = get_db()
    
    result = db.execute("SELECT SUM(quantity) FROM cart WHERE user_id = ?", (session['user_id'],)).fetchone()
    cart_count = result[0] if result and result[0] is not None else 0
    
    if search_query:
        query = "SELECT * FROM products WHERE name LIKE ? OR description LIKE ?"
        products = db.execute(query, (f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        products = db.execute("SELECT * FROM products").fetchall()
        
    return render_template('store.html', products=products, search_query=search_query, cart_count=cart_count)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    existing = db.execute("SELECT * FROM cart WHERE user_id = ? AND product_id = ?", (session['user_id'], product_id)).fetchone()
    
    if existing:
        db.execute("UPDATE cart SET quantity = quantity + 1 WHERE id = ?", (existing['id'],))
    else:
        db.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)", (session['user_id'], product_id))
    db.commit()
    
    return redirect(url_for('storefront'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('storefront'))
        
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('storefront'))
        else:
            flash('Invalid username or password configuration.', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            flash('Please populate all available validation fields.', 'error')
            return render_template('register.html')
            
        hashed_password = generate_password_hash(password)
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            db.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username is already taken by another profile.', 'error')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)