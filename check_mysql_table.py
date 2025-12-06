import mysql.connector

config = {
    'host': '8.138.24.168',
    'port': 3306,
    'user': 'gov_user',
    'password': '123456',
    'database': 'gov_web',
    'use_pure': True,
    'connection_timeout': 5
}

print(f"Checking MySQL table structure...")

try:
    conn = mysql.connector.connect(**config)
    if conn.is_connected():
        print("✅ MySQL Connection Successful!")
        cursor = conn.cursor()
        
        # Get table structure
        table_name = 'public_info'
        print(f"Checking table: {table_name}")
        cursor.execute(f"DESCRIBE {table_name};")
        columns = cursor.fetchall()
        
        print(f"\n📋 Table '{table_name}' columns:")
        for column in columns:
            print(f"- {column[0]}: {column[1]} (Null: {column[2]}, Key: {column[3]}, Default: {column[4]}, Extra: {column[5]})")
            
        # Check row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"\n📊 Total rows in '{table_name}': {count}")
        
        cursor.close()
        conn.close()
        print("\n✅ Table structure checked successfully.")
except mysql.connector.Error as err:
    print(f"❌ MySQL Connection Failed: {err}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
