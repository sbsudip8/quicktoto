from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import session
from flask import Flask, request, jsonify, render_template, redirect
import sqlite3

app = Flask(__name__)
app.secret_key = "quicktoto_secret"

# DATABASE CONNECTION
conn = sqlite3.connect(
    "database/quicktoto.db",
    check_same_thread=False
)

cursor = conn.cursor()


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

# GLOBAL VARIABLES
current_ride = None
ride_status = "No active ride"
assigned_driver = None



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

        "driver.html",

        driver=driver_data

    )

    return render_template("driver.html")




# REQUEST RIDE
@app.route("/request_ride", methods=["POST"])
def request_ride():

    global current_ride
    global ride_status
    global assigned_driver

    data = request.json

    pickup = data["pickup"]

    drop = data["drop"]

    ride_type = data["rideType"]

    fare = data["fare"]

    seats_requested = int(data["seats"])




    # GET ONLINE DRIVERS
    cursor.execute(

        '''

        SELECT *

        FROM drivers

        WHERE online = 1

        '''

    )



    drivers = cursor.fetchall()




    selected_driver = None




    # FIND AVAILABLE DRIVER
    for driver in drivers:

        available_seats = driver[9]



        # PRIVATE RIDE
        if ride_type == "Private":

            if available_seats == 5:

                selected_driver = driver

                break



        # SHARED RIDE
        else:

            if available_seats >= seats_requested:

                selected_driver = driver

                break




    # NO DRIVER FOUND
    if not selected_driver:

        return jsonify({

            "status": "No Toto Available"

        })




    # DRIVER FOUND
    driver_id = selected_driver[0]

    driver_name = selected_driver[3]



    # UPDATE AVAILABLE SEATS
    if ride_type == "Private":

        new_available = 0

    else:

        new_available = (

            selected_driver[9]

            - seats_requested

        )




    cursor.execute(

        '''

        UPDATE drivers

        SET available_seats = ?

        WHERE id = ?

        ''',

        (

            new_available,

            driver_id

        )

    )

    conn.commit()




    # SAVE CURRENT RIDE
    current_ride = data

    ride_status = "Searching for driver..."

    assigned_driver = driver_name




    # SAVE RIDE
    cursor.execute(

        '''

        INSERT INTO rides (

            pickup,

            drop_location,

            ride_type,

            fare,

            status

        )

        VALUES (?, ?, ?, ?, ?)

        ''',

        (

            str(pickup),

            str(drop),

            ride_type,

            fare,

            ride_status

        )

    )

    conn.commit()




    return jsonify({

        "status": ride_status,

        "driver": driver_name,

        "availableSeats": new_available

    })




# GET RIDE
@app.route("/get_ride")
def get_ride():

    global current_ride
    global ride_status
    global assigned_driver

    if current_ride:

        return jsonify({

            "ride": current_ride,
            "status": ride_status,
            "driver": assigned_driver

        })

    return jsonify({

        "message": "No rides"

    })

# ACCEPT RIDE
@app.route("/accept_ride", methods=["POST"])
def accept_ride():

    global ride_status
    global current_ride

    ride_status = "Ride Accepted"



    cursor.execute(

        '''

        UPDATE rides

        SET status = ?

        WHERE id = (

            SELECT MAX(id)
            FROM rides

        )

        ''',

        (ride_status,)

    )

    conn.commit()




    # CLEAR CURRENT RIDE
    current_ride = None




    return jsonify({

        "status": ride_status

    })

# REJECT RIDE
@app.route("/reject_ride", methods=["POST"])
def reject_ride():

    global ride_status
    global current_ride

    ride_status = "Ride Rejected"



    cursor.execute(

        '''

        UPDATE rides

        SET status = ?

        WHERE id = (

            SELECT MAX(id)
            FROM rides

        )

        ''',

        (ride_status,)

    )

    conn.commit()




    # CLEAR CURRENT RIDE
    current_ride = None




    return jsonify({

        "status": ride_status

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

    global ride_status

    ride_status = "Driver Reached Pickup"




    return jsonify({

        "status": ride_status

    })

# PASSENGER ONBOARD
@app.route(

    "/ride_onboard",

    methods=["POST"]

)

def ride_onboard():

    global ride_status

    ride_status = "Passenger Onboard"




    return jsonify({

        "status": ride_status

    })

# COMPLETE RIDE
@app.route(

    "/complete_ride",

    methods=["POST"]

)

def complete_ride():

    global ride_status
    global current_ride




    # GET LAST DRIVER
    cursor.execute(

        '''

        SELECT *

        FROM drivers

        WHERE first_name = ?

        ''',

        (assigned_driver,)

    )



    driver = cursor.fetchone()




    # RESTORE SEATS
    if driver:

        cursor.execute(

            '''

            UPDATE drivers

            SET available_seats = 5

            WHERE id = ?

            ''',

            (driver[0],)

        )

        conn.commit()




    ride_status = "Ride Completed"




    # CLEAR ACTIVE RIDE
    current_ride = None




    return jsonify({

        "status": ride_status

    })

if __name__ == "__main__":

    app.run(debug=True)