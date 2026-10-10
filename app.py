from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "super_secret_shopping_key_123"

def init_shop_db():
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone() == 0:
        sample_items = [
            ("Professional Developer Keyboard", 89.99, "Mechanical keys for fast and efficient typing."),
            ("Ergonomic Developer Mouse", 59.50, "Reduces wrist pain during long programming sessions."),
            ("Dual 4K Programming Monitor", 299.99, "Crisp text scaling layout viewports for clean bug checking.")
        ]
        cursor.executemany("INSERT INTO products (name, price, description) VALUES (?, ?, ?)", sample_items)
        
        hashed_pw = generate_password_hash("password123")
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", hashed_pw))
        except sqlite3.IntegrityError:
            pass
            
        conn.commit()
    conn.close()

init_shop_db()

@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
        
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, description FROM products")
    all_products = cursor.fetchall()
    conn.close()
    return render_template("store.html", products=all_products, username=session["user"])

# ==========================================
# NEW FEATURE: REGISTRATION (SIGN UP) ROUTE
# ==========================================
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    success = None
    if request.method == "POST":
        username_input = request.form.get("username").strip()
        password_input = request.form.get("password")
        
        if not username_input or not password_input:
            error = "Please fill out all input fields."
        else:
            conn = sqlite3.connect("store.db")
            cursor = conn.cursor()
            
            # Scramble the new user's password securely
            hashed_pw = generate_password_hash(password_input)
            
            try:
                # INSERT query operation: Save the newly generated user profile row data
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username_input, hashed_pw))
                conn.commit()
                success = "Account created successfully! You can now log in."
            except sqlite3.IntegrityError:
                # Triggers automatically if the text matches an existing UNIQUE username cell
                error = "That username is already taken. Please choose another one!"
            finally:
                conn.close()
                
    return render_template("register.html", error=error, success=success)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username_input = request.form.get("username")
        password_input = request.form.get("password")
        
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password_hash FROM users WHERE username = ?", (username_input,))
        user_record = cursor.fetchone()
        conn.close()
        
        if user_record and check_password_hash(user_record[1], password_input):
            session["user"] = user_record[0]
            return redirect(url_for("home"))
        else:
            error = "Invalid username or password. Try again!"
            
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)