from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
# A secret key is required by Flask to keep user sessions locked and secure
app.secret_key = "super_secret_shopping_key_123"

def init_shop_db():
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    
    # 1. Create the products table structure layout
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    """)
    
    # 2. NEW: Create a users table to store logins securely
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    
    # Inject default stock items if empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_items = [
            ("Professional Developer Keyboard", 89.99, "Mechanical keys for fast and efficient typing."),
            ("Ergonomic Developer Mouse", 59.50, "Reduces wrist pain during long programming sessions."),
            ("Dual 4K Programming Monitor", 299.99, "Crisp text scaling layout viewports for clean bug checking.")
        ]
        cursor.executemany("INSERT INTO products (name, price, description) VALUES (?, ?, ?)", sample_items)
        
        # Inject an initial test user profile safely (Username: admin | Password: password123)
        hashed_pw = generate_password_hash("password123")
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", hashed_pw))
        except sqlite3.IntegrityError:
            pass
            
        conn.commit()
    conn.close()

# Spin up database systems immediately
init_shop_db()

@app.route("/")
def home():
    # Defensive Check: If user isn't logged in, redirect them straight to the login panel
    if "user" not in session:
        return redirect(url_for("login"))
        
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, description FROM products")
    all_products = cursor.fetchall()
    conn.close()
    return render_template("store.html", products=all_products, username=session["user"])

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username_input = request.form.get("username")
        password_input = request.form.get("password")
        
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        # Find the record row for this username string input
        cursor.execute("SELECT username, password_hash FROM users WHERE username = ?", (username_input,))
        user_record = cursor.fetchone()
        conn.close()
        
        # Secure check matching the input password against the database scramble hash row
        if user_record and check_password_hash(user_record[1], password_input):
            session["user"] = user_record[0] # Create an active session key
            return redirect(url_for("home"))
        else:
            error = "Invalid username or password. Try again!"
            
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None) # Destroys the login session ticket securely
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)