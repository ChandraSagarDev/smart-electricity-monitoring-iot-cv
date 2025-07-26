import sqlite3
from datetime import datetime

# Initializes the SQLite database and creates required tables if they do not exist.
def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect('readings.db')
    c = conn.cursor()
    
    # Create table for KWh readings
    c.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reading TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            image_path TEXT,
            fixed_charge REAL,
            energy_charge REAL,
            tod_charge REAL,
            duty REAL,
            subsidy REAL,
            total_amount REAL
        )
    ''')
    
    conn.commit()
    conn.close()

def save_reading(reading, image_path=None, bill_details=None):
    """Save a new reading to the database."""
    conn = sqlite3.connect('readings.db')
    c = conn.cursor()
    
    if bill_details:
        c.execute('''
            INSERT INTO readings (
                reading, image_path, fixed_charge, energy_charge, 
                tod_charge, duty, subsidy, total_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            reading, image_path, 
            bill_details['fixed_charge'], bill_details['energy_charge'],
            bill_details['tod_charge'], bill_details['duty'],
            bill_details['subsidy'], bill_details['final']
        ))
    else:
        c.execute('INSERT INTO readings (reading, image_path) VALUES (?, ?)',
                  (reading, image_path))
    
    conn.commit()
    conn.close()

def get_readings(limit=50):
    """Get the most recent readings from the database."""
    conn = sqlite3.connect('readings.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT reading, timestamp, image_path, 
               fixed_charge, energy_charge, tod_charge, 
               duty, subsidy, total_amount 
        FROM readings 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    readings = c.fetchall()
    conn.close()
    
    return readings
