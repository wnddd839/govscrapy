import mysql.connector
import sys

config = {
    'host': '8.138.24.168',
    'port': 3306,
    'user': 'gov_user',
    'password': '123456',
    'database': 'gov_open',
    'use_pure': True, # Force pure python
    'connection_timeout': 5
}

print(f"Testing MySQL connection to {config['host']}:{config['port']}...")

try:
    conn = mysql.connector.connect(**config)
    if conn.is_connected():
        print("✅ MySQL Connection Successful!")
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        record = cursor.fetchone()
        print(f"Connected to database: {record[0]}")
        
        # Check table
        cursor.execute("SHOW TABLES LIKE 'gov_open_data';")
        table = cursor.fetchone()
        if table:
            print("✅ Table 'gov_open_data' exists.")
        else:
            print("⚠️ Table 'gov_open_data' does not exist.")
            
        cursor.close()
        conn.close()
except mysql.connector.Error as err:
    print(f"❌ MySQL Connection Failed: {err}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
