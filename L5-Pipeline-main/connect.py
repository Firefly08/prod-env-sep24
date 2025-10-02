import sqlite3
import pandas as pd

# Connect to the database (created from init_db.sql)
conn = sqlite3.connect('data.db')

# Read and display table contents
df = pd.read_sql_query("SELECT * FROM users;", conn)
print(df)

conn.close()