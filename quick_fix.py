import sqlite3

# CONNECT DATABASE
conn = sqlite3.connect(
    "database/quicktoto.db"
)

cursor = conn.cursor()

print("Cleaning Quicktoto database...")

# DELETE BOOKINGS
cursor.execute(
    "DELETE FROM bookings"
)

# DELETE DISPATCH HISTORY
cursor.execute(
    "DELETE FROM dispatch_history"
)

# RESET DRIVER SEATS
cursor.execute(
    '''
    UPDATE drivers
    SET available_seats = total_seats
    '''
)

conn.commit()

print("Database cleaned successfully.")

conn.close()