from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

# This helper function automatically builds our shop database and lists sample stock items
def init_shop_db():
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    
    # Create the products table structure layout
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image_url TEXT
        )
    """)
    
    # Check if we already have items inside the store database row data
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        # If empty rows, inject 3 clean initial stock samples automatically
        sample_items = [
            ("Professional Developer Keyboard", 89.99, "Mechanical keys for fast and efficient typing.", "https://unsplash.com"),
            ("Ergonomic Developer Mouse", 59.50, "Reduces wrist pain during long programming sessions.", "https://unsplash.com"),
            ("Dual 4K Programming Monitor", 299.99, "Crisp text scaling layout viewports for clean bug checking.", "https://unsplash.com")
        ]
        cursor.executemany("INSERT INTO products (name, price, description, image_url) VALUES (?, ?, ?, ?)", sample_items)
        conn.commit()
        
    conn.close()

# Spin up the catalog setup database file on our server hard drive automatically
init_shop_db()

@app.route("/")
def home():
    # SELECT query operation: Pull the product list row data out of our relational tables
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, description, image_url FROM products")
    all_products = cursor.fetchall()
    conn.close()
    
    # Send the products catalog straight into the HTML file dashboard view
    return render_template("store.html", products=all_products)

if __name__ == "__main__":
    app.run(debug=True)