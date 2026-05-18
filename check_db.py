import sqlite3

conn = sqlite3.connect("database/quicktoto.db")

cursor = conn.cursor()


# SHOW USERS
cursor.execute("SELECT * FROM users")

users = cursor.fetchall()

print("\nUSERS TABLE:\n")

for user in users:

    print(user)


# SHOW DRIVERS
cursor.execute("SELECT * FROM drivers")

drivers = cursor.fetchall()

print("\nDRIVERS TABLE:\n")

for driver in drivers:

    print(driver)