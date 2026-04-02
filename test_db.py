import sqlite3
import json

conn = sqlite3.connect('newbirth_church.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 5")
rows = cur.fetchall()
for row in rows:
    print(dict(row))
