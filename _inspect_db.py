import sqlite3

conn = sqlite3.connect("db.sqlite3")
cur = conn.cursor()
print("tables:", cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
print("product cols:", cur.execute("PRAGMA table_info(store_product)").fetchall())
print("order cols:", cur.execute("PRAGMA table_info(store_order)").fetchall())
print("shipping cols:", cur.execute("PRAGMA table_info(store_shippingaddress)").fetchall())
print("migrations:", cur.execute("SELECT app, name FROM django_migrations WHERE app='store'").fetchall())
conn.close()
