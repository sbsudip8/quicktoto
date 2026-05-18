import sqlite3

conn = sqlite3.connect(

    "database/quicktoto.db"

)

cursor = conn.cursor()


# RESET ALL DRIVER SEATS
cursor.execute(

    '''

    UPDATE drivers

    SET available_seats = 5

    '''

)

conn.commit()


print(

    "✅ All driver seats reset to 5"

)

conn.close()