import pandas as pd
import mysql.connector

# Read CSV file
df = pd.read_csv("job_details_final3.csv")

host = 'localhost'
user = 'root'
password = 'Password@082810'
database = 'jobs_db'

# Connect to MySQL
conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
cursor = conn.cursor()

# Truncate the table to delete all existing data
cursor.execute("TRUNCATE TABLE job_details")

sql = """
    INSERT IGNORE INTO job_details(title, company, city, province, country, posting_time, skills) 
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

# Replace 'NaN' values with empty strings in all columns
df = df.fillna('')

# Filter out rows with invalid date values ('0000-00-00 00:00:00')
df = df[df['posting_time'] != '0000-00-00 00:00:00']

# Convert 'posting_time' column to datetime format
df['posting_time'] = pd.to_datetime(df['posting_time']).dt.strftime('%Y-%m-%d')

# Insert new data into the table
for index, row in df.iterrows():
    values = tuple(row)
    print("Inserting")
    cursor.execute(sql, values)

conn.commit()
cursor.close()
conn.close()
print("Data imported successfully.")
