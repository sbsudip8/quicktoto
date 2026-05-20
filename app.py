from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import session
from flask import Flask, request, jsonify, render_template, redirect
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
app.secret_key = "quicktoto_secret"

# DATABASE CONNECTION
conn = sqlite3.connect(
    "database/quicktoto.db",
    check_same_thread=False
)

cursor = conn.cursor()

# TEMP DRIVER QUEUES
driver_queues = {}

# CREATE TABLE
cursor.execute('''

CREATE TABLE IF NOT EXISTS rides (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    pickup TEXT,
    drop_location TEXT,
    ride_type TEXT,
    fare TEXT,
    status TEXT

)

''')

conn.commit()

# TOTO TABLE
cursor.execute('''

CREATE TABLE IF NOT EXISTS totos (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    driver_name TEXT,

    total_seats INTEGER,

    available_seats INTEGER

)

''')

conn.commit()

# USERS TABLE
cursor.execute('''

CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    first_name TEXT,

    last_name TEXT,

    phone TEXT,

    email TEXT,

    username TEXT UNIQUE,

    password TEXT,

    role TEXT

)

''')

conn.commit()

# DRIVERS TABLE
cursor.execute('''

CREATE TABLE IF NOT EXISTS drivers (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER,

    license_id TEXT,

    first_name TEXT,

    last_name TEXT,

    phone TEXT,

    email TEXT,

    toto_number TEXT,

    total_seats INTEGER,

    available_seats INTEGER,

    latitude REAL,

    longitude REAL,

    online INTEGER

)

''')

conn.commit()

# RIDES TABLE
cursor.execute('''

CREATE TABLE IF NOT EXISTS rides (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ride_id TEXT,

    driver_id INTEGER,

    ride_type TEXT,

    total_seats INTEGER,

    available_seats INTEGER,

    status TEXT

)

''')

conn.commit()

# BOOKINGS TABLE
cursor.execute('''

CREATE TABLE IF NOT EXISTS bookings (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    booking_id TEXT,

    ride_id TEXT,

    passenger_id INTEGER,

    driver_id INTEGER,

    pickup TEXT,

    drop_location TEXT,

    ride_type TEXT,

    seats INTEGER,

    fare TEXT,

    status TEXT,

    queue_position INTEGER DEFAULT 0,
               
    assigned_time TEXT

)

''')

conn.commit()

# DISPATCH HISTORY
cursor.execute('''

CREATE TABLE IF NOT EXISTS dispatch_history (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    booking_id TEXT,

    driver_id INTEGER,

    reject_count INTEGER DEFAULT 0,

    blocked_until TEXT

)

''')

conn.commit()

# GLOBAL VARIABLES
# current_ride = None
# ride_status = "No active ride"
# assigned_driver = None



# PUBLIC LANDING PAGE
@app.route("/")
def landing():

    # USER ALREADY LOGGED IN
    if "user_id" in session:

        # PASSENGER
        if session["role"] == "passenger":

            return redirect(

                "/passenger"

            )



        # DRIVER
        if session["role"] == "driver":

            return redirect(

                "/driver"

            )



    # NOT LOGGED IN
    return render_template(

        "index.html"

    )




# PASSENGER DASHBOARD
@app.route("/passenger")
def passenger_dashboard():

    # NOT LOGGED IN
    if "user_id" not in session:

        return redirect(

            "/login/passenger"

        )



    # WRONG ROLE
    if session["role"] != "passenger":

        return redirect(

            "driver"

        )



    user_id = session["user_id"]




    # GET USER INFO
    cursor.execute(

        '''

        SELECT *

        FROM users

        WHERE id = ?

        ''',

        (user_id,)

    )



    user_data = cursor.fetchone()




    return render_template(

        "passenger_dashboard.html",

        user=user_data

    )



# DRIVER PAGE
@app.route("/driver")

# DRIVER DASHBOARD
@app.route("/driver")
def driver():

    # NOT LOGGED IN
    if "user_id" not in session:

        return redirect(

            "/login/driver"

        )



    # WRONG ROLE
    if session["role"] != "driver":

        return redirect(

            "passenger"

        )



    user_id = session["user_id"]




    # GET DRIVER INFO
    cursor.execute(

        '''

        SELECT *

        FROM drivers

        WHERE user_id = ?

        ''',

        (user_id,)

    )



    driver_data = cursor.fetchone()




    return render_template(

        "driver_dashboard.html",

        driver=driver_data

    )

    return render_template("driver_dashboard.html")




# REQUEST RIDE
@app.route(

    "/request_ride",

    methods=["POST"]

)

def request_ride():

    data = request.json




    pickup = data["pickup"]

    drop = data["drop"]

    ride_type = data["rideType"]

    fare = data["fare"]

    seats_requested = int(

        data["seats"]

    )




    # PASSENGER
    passenger_id = session["user_id"]




    # CREATE BOOKING ID
    cursor.execute(

        "SELECT COUNT(*) FROM bookings"

    )



    total_bookings = cursor.fetchone()[0]



    booking_id = (

        "B"

        + str(total_bookings + 1)

    )

    # FIND ELIGIBLE DRIVERS
    cursor.execute(

        '''

        SELECT *

        FROM drivers

        WHERE online = 1

        '''

    )

    drivers = cursor.fetchall()

    # FIND ELIGIBLE DRIVERS
    cursor.execute(

        '''

        SELECT *

        FROM drivers

        WHERE online = 1

        '''

    )

    drivers = cursor.fetchall()




    eligible_drivers = []

    # FILTER ELIGIBLE DRIVERS
    for driver in drivers:

        driver_id = driver[0]



        # CHECK DRIVER BLOCK
        cursor.execute(

            '''

            SELECT *

            FROM dispatch_history

            WHERE driver_id = ?

            ORDER BY id DESC

            LIMIT 1

            ''',

            (driver_id,)

        )



        history = cursor.fetchone()




        # DRIVER TEMP BLOCKED
        if history:

            blocked_until = history[4]



            if blocked_until:

                blocked_dt = datetime.fromisoformat(

                    blocked_until

                )



                # STILL BLOCKED
                if datetime.now() < blocked_dt:

                    continue




        available_seats = driver[9]



        # PRIVATE RIDE
        if ride_type == "Private":

            if available_seats == 5:

                eligible_drivers.append(driver)




        # SHARED RIDE
        else:

            if available_seats >= seats_requested:

                eligible_drivers.append(driver)

    
    # NO ELIGIBLE DRIVERS
    if len(eligible_drivers) == 0:

        return jsonify({

            "status": "No Toto Available"

        })




    # SORT BY AVAILABLE SEATS
    # Shared rides with fewer remaining seats
    # get higher priority first

    eligible_drivers.sort(

        key=lambda d: d[9]

    )

    # SAVE DRIVER QUEUE
    driver_queue = []

    for driver in eligible_drivers:

        driver_queue.append(

            driver[0]

        )


    # HIGHEST PRIORITY DRIVER
    selected_driver = eligible_drivers[0]

    assigned_driver_id = selected_driver[0]

    # STORE QUEUE
    driver_queues[booking_id] = driver_queue

    # SAVE BOOKING
    cursor.execute(

        '''

        INSERT INTO bookings (

            booking_id,

            ride_id,

            passenger_id,

            driver_id,

            pickup,

            drop_location,

            ride_type,

            seats,

            fare,

            status

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ''',

        (

            booking_id,

            None,

            passenger_id,

            assigned_driver_id,

            str(pickup),

            str(drop),

            ride_type,

            seats_requested,

            fare,

            "pending",

            0,

            datetime.now().isoformat()

        )

    )



    conn.commit()




    return jsonify({

        "status": "Booking Created",

        "booking_id": booking_id

    })




# GET DRIVER BOOKINGS
@app.route("/get_ride")
def get_ride():

    # DRIVER USER ID
    user_id = session["user_id"]




    # FIND DRIVER
    cursor.execute(

        '''

        SELECT *

        FROM drivers

        WHERE user_id = ?

        ''',

        (user_id,)

    )



    driver = cursor.fetchone()




    if not driver:

        return jsonify({

            "ride": None

        })




    driver_id = driver[0]




    # GET PENDING BOOKING
    cursor.execute(

        '''

        SELECT *

        FROM bookings

        WHERE driver_id = ?
        AND status = 'pending'

        LIMIT 1

        ''',

        (driver_id,)

    )



    booking = cursor.fetchone()




    if not booking:

        return jsonify({

            "ride": None

        })




    return jsonify({

        "ride": {

            "booking_id": booking[1],

            "pickup": booking[4],

            "drop": booking[5],

            "rideType": booking[6],

            "seats": booking[7],

            "fare": booking[8]

        }

    })

# ACCEPT RIDE
@app.route(

    "/accept_ride",

    methods=["POST"]

)

def accept_ride():

    data = request.json

    booking_id = data["booking_id"]




    # GET BOOKING
    cursor.execute(

        '''

        SELECT *

        FROM bookings

        WHERE booking_id = ?

        ''',

        (booking_id,)

    )



    booking = cursor.fetchone()




    if not booking:

        return jsonify({

            "status": "Booking Not Found"

        })

    # ONLY PENDING BOOKINGS CAN BE ACCEPTED
    if booking[10] != "pending":

        return jsonify({

            "status": "Already Taken"

        })

    # GET BOOKING SEATS
    seats_requested = booking[8]

    driver_id = booking[4]




    # REDUCE DRIVER SEATS
    cursor.execute(

        '''

        UPDATE drivers

        SET available_seats =

            available_seats - ?

        WHERE id = ?

        ''',

        (

            seats_requested,

            driver_id

        )

    )

    # ACCEPT BOOKING SAFELY
    cursor.execute(

        '''

        UPDATE bookings

        SET status = 'accepted'

        WHERE booking_id = ?
        AND status = 'pending'

        ''',

        (booking_id,)

    )

    conn.commit()

    return jsonify({

        "status": "Ride Accepted"

    })

# REJECT RIDE
@app.route(

    "/reject_ride",

    methods=["POST"]

)

def reject_ride():

    data = request.json

    booking_id = data["booking_id"]




    # GET QUEUE
    queue = driver_queues.get(

        booking_id,

        []

    )




    # FIND BOOKING
    cursor.execute(

        '''

        SELECT *

        FROM bookings

        WHERE booking_id = ?

        ''',

        (booking_id,)

    )



    booking = cursor.fetchone()
    driver_id = booking[4]




    if not booking:

        return jsonify({

            "status": "Booking Not Found"

        })




    current_position = booking[11]


    # CHECK DISPATCH HISTORY
    cursor.execute(

        '''

        SELECT *

        FROM dispatch_history

        WHERE booking_id = ?
        AND driver_id = ?

        ''',

        (

            booking_id,

            driver_id

        )

    )

    history = cursor.fetchone()




    # HISTORY EXISTS
    if history:

        reject_count = history[3] + 1




        # BLOCK AFTER 2 REJECTS
        blocked_until = None

        if reject_count >= 2:

            blocked_until = (

                datetime.now()

                + timedelta(minutes=30)

            ).isoformat()




        cursor.execute(

            '''

            UPDATE dispatch_history

            SET reject_count = ?,
                blocked_until = ?

            WHERE id = ?

            ''',

            (

                reject_count,

                blocked_until,

                history[0]

            )

        )

    # FIRST REJECTION
    else:

        cursor.execute(

            '''

            INSERT INTO dispatch_history (

                booking_id,

                driver_id,

                reject_count,

                blocked_until

            )

            VALUES (?, ?, ?, ?)

            ''',

            (

                booking_id,

                driver_id,

                1,

                None

            )

        )

    conn.commit()

    # NEXT DRIVER
    next_position = current_position + 1

    # NO MORE DRIVERS
    if next_position >= len(queue):

        return jsonify({

            "status": "No More Drivers"

        })




    next_driver_id = queue[next_position]




    # UPDATE BOOKING
    cursor.execute(

        '''

        UPDATE bookings

        SET driver_id = ?,
            queue_position = ?

        WHERE booking_id = ?

        ''',

        (

            next_driver_id,

            next_position,

            booking_id
        )
    )

    conn.commit()

    return jsonify({

        "status": "Moved To Next Driver"

    })

# GET RIDE STATUS
@app.route("/ride_status")
def get_ride_status():

    global ride_status
    global assigned_driver

    return jsonify({

        "status": ride_status,
        "driver": assigned_driver

    })




# RIDE HISTORY
@app.route("/ride_history")
def ride_history():

    cursor.execute(

        '''

        SELECT *
        FROM rides

        ORDER BY id DESC

        '''

    )

    rides = cursor.fetchall()

    history = []

    for ride in rides:

        history.append({

            "id": ride[0],
            "pickup": ride[1],
            "drop": ride[2],
            "rideType": ride[3],
            "fare": ride[4],
            "status": ride[5]

        })

    return jsonify(history)

# CHOOSE SIGNUP
@app.route("/signup")
def choose_signup():

    return render_template(

        "choose_signup.html"

    )

# PASSENGER SIGNUP
@app.route(

    "/signup/passenger",

    methods=["GET", "POST"]

)

def passenger_signup():

    if request.method == "POST":

        first_name = request.form["first_name"]

        last_name = request.form["last_name"]

        phone = request.form["phone"]

        email = request.form["email"]

        username = request.form["username"]

        password = request.form["password"]




        # HASH PASSWORD
        hashed_password = generate_password_hash(

            password

        )



        try:

            cursor.execute(

                '''

                INSERT INTO users (

                    first_name,

                    last_name,

                    phone,

                    email,

                    username,

                    password,

                    role

                )

                VALUES (?, ?, ?, ?, ?, ?, ?)

                ''',

                (

                    first_name,

                    last_name,

                    phone,

                    email,

                    username,

                    hashed_password,

                    "passenger"

                )

            )

            conn.commit()




            return redirect(

                "/login/passenger"

            )



        except Exception as e:

            return str(e)




    return render_template(

        "passenger_signup.html"

    )

# DRIVER SIGNUP
@app.route(

    "/signup/driver",

    methods=["GET", "POST"]

)

def driver_signup():

    if request.method == "POST":

        license_id = request.form["license_id"]

        first_name = request.form["first_name"]

        last_name = request.form["last_name"]

        phone = request.form["phone"]

        email = request.form["email"]

        username = request.form["username"]

        password = request.form["password"]




        # HASH PASSWORD
        hashed_password = generate_password_hash(

            password

        )



        try:

            # INSERT USER
            cursor.execute(

                '''

                INSERT INTO users (

                    first_name,

                    last_name,

                    phone,

                    email,

                    username,

                    password,

                    role

                )

                VALUES (?, ?, ?, ?, ?, ?, ?)

                ''',

                (

                    first_name,

                    last_name,

                    phone,

                    email,

                    username,

                    hashed_password,

                    "driver"

                )

            )

            conn.commit()




            # GET USER ID
            user_id = cursor.lastrowid




            # INSERT DRIVER PROFILE
            cursor.execute(

                '''

                INSERT INTO drivers (

                    user_id,

                    license_id,

                    first_name,

                    last_name,

                    phone,

                    email,

                    toto_number,

                    total_seats,

                    available_seats,

                    latitude,

                    longitude,

                    online

                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ''',

                (

                    user_id,

                    license_id,

                    first_name,

                    last_name,

                    phone,

                    email,

                    "QT-" + str(user_id),

                    5,

                    5,

                    0,

                    0,

                    0

                )

            )

            conn.commit()




            return redirect(

                "/login/driver"

            )



        except Exception as e:

            return str(e)




    return render_template(

        "driver_signup.html"

    )

# CHOOSE LOGIN
@app.route("/login")
def choose_login():

    return render_template(

        "choose_login.html"

    )

# PASSENGER LOGIN
@app.route(

    "/login/passenger",

    methods=["GET", "POST"]

)

def passenger_login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]



        # FIND USER
        cursor.execute(

            '''

            SELECT *
            FROM users

            WHERE username = ?

            AND role = ?

            ''',

            (

                username,
                "passenger"

            )

        )



        user = cursor.fetchone()




        # VERIFY PASSWORD
        if user and check_password_hash(

            user[6],
            password

        ):



            # SAVE SESSION
            session["user_id"] = user[0]

            session["username"] = user[1]

            session["role"] = user[7]



            return redirect(

                "/passenger"

            )



        else:

            return "Invalid passenger credentials"



    return render_template(

        "passenger_login.html"

    )

# DRIVER LOGIN
@app.route(

    "/login/driver",

    methods=["GET", "POST"]

)

def driver_login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]



        # FIND DRIVER
        cursor.execute(

            '''

            SELECT *
            FROM users

            WHERE username = ?

            AND role = ?

            ''',

            (

                username,
                "driver"

            )

        )



        user = cursor.fetchone()




        # VERIFY PASSWORD
        if user and check_password_hash(

            user[6],
            password

        ):



            # SAVE SESSION
            session["user_id"] = user[0]

            session["username"] = user[1]

            session["role"] = user[7]



            return redirect(

                "/driver"

            )



        else:

            return "Invalid driver credentials"



    return render_template(

        "driver_login.html"

    )

# TOGGLE DRIVER STATUS
@app.route(

    "/toggle_driver_status",

    methods=["POST"]

)

def toggle_driver_status():

    # CHECK LOGIN
    if "user_id" not in session:

        return jsonify({

            "error": "Not logged in"

        })



    user_id = session["user_id"]



    data = request.json

    online = data["online"]




    # UPDATE DRIVER STATUS
    cursor.execute(

        '''

        UPDATE drivers

        SET online = ?

        WHERE user_id = ?

        ''',

        (

            1 if online else 0,

            user_id

        )

    )

    conn.commit()




    return jsonify({

        "success": True,

        "online": online

    })

# GET ONLINE DRIVERS
@app.route("/get_online_drivers")
def get_online_drivers():

    cursor.execute(

        '''

        SELECT *

        FROM drivers

        WHERE online = 1

        '''

    )



    drivers = cursor.fetchall()




    online_drivers = []



    for driver in drivers:

        online_drivers.append({

            "id": driver[0],

            "user_id": driver[1],

            "license_id": driver[2],

            "first_name": driver[3],

            "last_name": driver[4],

            "phone": driver[5],

            "email": driver[6],

            "toto_number": driver[7],

            "total_seats": driver[8],

            "available_seats": driver[9],

            "latitude": driver[10],

            "longitude": driver[11]

        })



    return jsonify(

        online_drivers

    )

# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect(

        "/"

    )

# UPDATE DRIVER LOCATION
@app.route(

    "/update_driver_location",

    methods=["POST"]

)

def update_driver_location():

    # NOT LOGGED IN
    if "user_id" not in session:

        return jsonify({

            "error": "Not logged in"

        })



    user_id = session["user_id"]



    data = request.json

    latitude = data["latitude"]

    longitude = data["longitude"]




    # UPDATE DB
    cursor.execute(

        '''

        UPDATE drivers

        SET latitude = ?,
            longitude = ?

        WHERE user_id = ?

        ''',

        (

            latitude,
            longitude,
            user_id

        )

    )

    conn.commit()




    return jsonify({

        "success": True

    })

# DRIVER ARRIVED
@app.route(

    "/ride_arrived",

    methods=["POST"]

)

def ride_arrived():

    data = request.json

    booking_id = data["booking_id"]




    cursor.execute(

        '''

        UPDATE bookings

        SET status = 'arrived'

        WHERE booking_id = ?

        ''',

        (booking_id,)

    )



    conn.commit()




    return jsonify({

        "status": "arrived"

    })

# PASSENGER ONBOARD
@app.route(

    "/ride_onboard",

    methods=["POST"]

)

def ride_onboard():

    data = request.json

    booking_id = data["booking_id"]




    cursor.execute(

        '''

        UPDATE bookings

        SET status = 'onboard'

        WHERE booking_id = ?

        ''',

        (booking_id,)

    )



    conn.commit()




    return jsonify({

        "status": "onboard"

    })

# COMPLETE RIDE
@app.route(

    "/complete_ride",

    methods=["POST"]

)

def complete_ride():

    data = request.json

    booking_id = data["booking_id"]




    # GET BOOKING
    cursor.execute(

        '''

        SELECT *

        FROM bookings

        WHERE booking_id = ?

        ''',

        (booking_id,)

    )



    booking = cursor.fetchone()




    if not booking:

        return jsonify({

            "status": "Booking Not Found"

        })




    seats_to_restore = booking[8]

    driver_id = booking[4]




    # UPDATE BOOKING STATUS
    cursor.execute(

        '''

        UPDATE bookings

        SET status = 'completed'

        WHERE booking_id = ?

        ''',

        (booking_id,)

    )




    # RESTORE SEATS
    cursor.execute(

        '''

        UPDATE drivers

        SET available_seats =

            available_seats + ?

        WHERE id = ?

        ''',

        (

            seats_to_restore,

            driver_id

        )

    )



    conn.commit()




    return jsonify({

        "status": "completed"

    })

# BOOKING STATUS
@app.route(

    "/booking_status/<booking_id>"

)

def booking_status(

    booking_id

):

    cursor.execute(

        '''

        SELECT *

        FROM bookings

        WHERE booking_id = ?

        ''',

        (booking_id,)

    )



    booking = cursor.fetchone()




    if not booking:

        return jsonify({

            "status": "Not Found"

        })




    return jsonify({

        "status": booking[10]

    })

# CHECK BOOKING TIMEOUT
@app.route("/check_timeout")
def check_timeout():

    from datetime import datetime




    # GET PENDING BOOKINGS
    cursor.execute(

        '''

        SELECT *

        FROM bookings

        WHERE status = 'pending'

        '''

    )



    bookings = cursor.fetchall()




    for booking in bookings:

        booking_id = booking[1]

        assigned_time = booking[12]




        if not assigned_time:

            continue




        assigned_dt = datetime.fromisoformat(

            assigned_time

        )



        now = datetime.now()




        seconds = (

            now - assigned_dt

        ).total_seconds()




        # 45 SECOND TIMEOUT
        if seconds >= 45:

            queue = driver_queues.get(

                booking_id,

                []

            )




            current_position = booking[11]

            next_position = current_position + 1




            # NEXT DRIVER EXISTS
            if next_position < len(queue):

                next_driver_id = queue[next_position]




                cursor.execute(

                    '''

                    UPDATE bookings

                    SET driver_id = ?,
                        queue_position = ?,
                        assigned_time = ?

                    WHERE booking_id = ?

                    ''',

                    (

                        next_driver_id,

                        next_position,

                        datetime.now().isoformat(),

                        booking_id

                    )

                )



                conn.commit()

    return jsonify({

        "status": "Timeout Check Complete"

    })

if __name__ == "__main__":

    app.run(debug=True)