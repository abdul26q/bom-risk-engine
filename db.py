import sqlite3
import os

DB_DIR = "data"
DB_FILE = os.path.join(DB_DIR, "component_cache.db")

def init_db():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS components (
            mpn TEXT PRIMARY KEY,
            manufacturer TEXT,
            category TEXT,
            description TEXT,
            lifecycle_status TEXT,
            package TEXT,
            max_voltage TEXT,
            max_current TEXT,
            price TEXT,
            source TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_cached_component(mpn):
    if not os.path.exists(DB_FILE):
        return None
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM components WHERE UPPER(mpn) = UPPER(?)", (mpn.strip(),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "MPN": row[0],
            "Manufacturer": row[1],
            "Category": row[2],
            "Description": row[3],
            "Lifecycle_Status": row[4],
            "Package": row[5],
            "Max_Voltage_V": row[6],
            "Max_Current_A": row[7],
            "Price_USD": row[8],
            "Source": row[9]
        }
    return None

def cache_component(data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO components VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("MPN"),
        data.get("Manufacturer", "N/A"),
        data.get("Category", "N/A"),
        data.get("Description", "N/A"),
        data.get("Lifecycle_Status", "Unknown"),
        data.get("Package", "N/A"),
        data.get("Max_Voltage_V", "N/A"),
        data.get("Max_Current_A", "N/A"),
        data.get("Price_USD", "N/A"),
        data.get("Source", "API/Search")
    ))
    conn.commit()
    conn.close()
