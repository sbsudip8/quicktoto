let map;

let pickupMarker;
let dropMarker;

let pickupLocation = null;
let dropLocation = null;

let routingControl;


// REAL DRIVER MARKERS
let driverMarkers = [];


const gpsBtn = document.getElementById("gpsBtn");
const requestBtn = document.getElementById("requestBtn");




// GET GPS LOCATION
gpsBtn.onclick = () => {

    navigator.geolocation.getCurrentPosition(

        position => {

            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            pickupLocation = { lat, lng };



            document.getElementById(

                "pickupText"

            ).innerText =

                lat.toFixed(5) +

                ", " +

                lng.toFixed(5);




            initMap(lat, lng);

        }

    );

};




// INITIALIZE MAP
function initMap(lat, lng) {

    // REMOVE OLD MAP
    if (map) {

        map.remove();

    }



    // CREATE MAP
    map = L.map('map').setView([lat, lng], 15);




    // TILE LAYER
    L.tileLayer(

        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',

        {

            attribution: '© OpenStreetMap'

        }

    ).addTo(map);




    // PICKUP MARKER
    pickupMarker = L.marker([lat, lng])

        .addTo(map)

        .bindPopup("📍 You are here")

        .openPopup();




    // CLICK TO SET DROP
    map.on('click', function(e) {

        // REMOVE OLD DROP
        if (dropMarker) {

            map.removeLayer(dropMarker);

        }



        // SAVE LOCATION
        dropLocation = {

            lat: e.latlng.lat,
            lng: e.latlng.lng

        };




        // DROP MARKER
        dropMarker = L.marker([

            dropLocation.lat,
            dropLocation.lng

        ])

        .addTo(map)

        .bindPopup("🏁 Drop Location")

        .openPopup();




        // UPDATE UI
        document.getElementById(

            "dropText"

        ).innerText =

            dropLocation.lat.toFixed(5) +

            ", " +

            dropLocation.lng.toFixed(5);




        // DRAW ROUTE
        drawRoute();



        // UPDATE FARE
        updateFare();

    });




    // LOAD ONLINE DRIVERS
    loadOnlineDrivers();



    // REFRESH DRIVERS
    setInterval(

        loadOnlineDrivers,

        5000

    );

}




// DRAW ROUTE
function drawRoute() {

    // REMOVE OLD ROUTE
    if (routingControl) {

        map.removeControl(routingControl);

    }



    routingControl = L.Routing.control({

        waypoints: [

            L.latLng(

                pickupLocation.lat,
                pickupLocation.lng

            ),

            L.latLng(

                dropLocation.lat,
                dropLocation.lng

            )

        ],

        routeWhileDragging: false,

        draggableWaypoints: false,

        addWaypoints: false,

        show: false

    }).addTo(map);

}




// DISTANCE CALCULATION
function calculateDistance(lat1, lng1, lat2, lng2) {

    let dx = lat1 - lat2;
    let dy = lng1 - lng2;

    return Math.sqrt(dx * dx + dy * dy);

}




// UPDATE FARE
function updateFare() {

    if (!pickupLocation || !dropLocation) {

        return;

    }



    let distance = calculateDistance(

        pickupLocation.lat,
        pickupLocation.lng,

        dropLocation.lat,
        dropLocation.lng

    );



    // APPROX KM
    distance = distance * 111;




    // GET RIDE TYPE
    let rideType = document.querySelector(

        'input[name="rideType"]:checked'

    ).value;




    let fare;



    if (rideType === "Private") {

        fare = 30 + (distance * 10);

    }

    else {

        fare = 15 + (distance * 5);

    }



    fare = Math.round(fare);




    document.getElementById(

        "fareText"

    ).innerText = "₹" + fare;

}




// UPDATE FARE ON TYPE CHANGE
document.querySelectorAll(

    'input[name="rideType"]'

).forEach(radio => {

    radio.addEventListener(

        'change',

        updateFare

    );

});




// REQUEST RIDE
requestBtn.onclick = async () => {

    if (!pickupLocation || !dropLocation) {

        alert(

            "Please set pickup and drop locations"

        );

        return;

    }



    let rideType = document.querySelector(

        'input[name="rideType"]:checked'

    ).value;




    // SEND TO BACKEND
    await fetch(

        "/request_ride",

        {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify({

                pickup: pickupLocation,

                drop: dropLocation,

                rideType: rideType,

                fare: document.getElementById(

                    "fareText"

                ).innerText

            })

        }

    );



    alert(

        "🔍 Searching for Toto Driver..."

    );

};




// LIVE STATUS
let lastStatus = "";



async function checkRideStatus() {

    let response = await fetch(

        "/ride_status"

    );



    let data = await response.json();




    // UPDATE STATUS TEXT
    document.getElementById(

        "rideStatus"

    ).innerText = data.status;




    // DRIVER INFO
    document.getElementById(

        "driverInfo"

    ).innerText = data.driver || "";




    // STATUS CHANGE POPUPS
    if (data.status !== lastStatus) {

        if (data.status === "Ride Accepted") {

            alert(

                "✅ Your ride has been accepted!"

            );

        }



        if (data.status === "Ride Rejected") {

            alert(

                "❌ Your ride was rejected."

            );

        }



        lastStatus = data.status;

    }

}




// ONLINE DRIVERS
async function loadOnlineDrivers() {

    // MAP NOT READY
    if (!map) {

        return;

    }




    // REMOVE OLD MARKERS
    driverMarkers.forEach(marker => {

        map.removeLayer(marker);

    });

    driverMarkers = [];




    // FETCH ONLINE DRIVERS
    let response = await fetch(

        "/get_online_drivers"

    );



    let drivers = await response.json();




    // ADD DRIVER MARKERS
    drivers.forEach(driver => {

        // SKIP EMPTY GPS
        if (

            driver.latitude === 0 ||

            driver.longitude === 0

        ) {

            return;

        }




        let marker = L.marker([

            driver.latitude,

            driver.longitude

        ])

        .addTo(map)

        .bindPopup(

            `

            🚖 ${driver.first_name}<br>

            Toto ID:

            ${driver.toto_number}<br>

            Available Seats:

            ${driver.available_seats}

            `

        );



        driverMarkers.push(marker);

    });

}




// CHECK STATUS EVERY 2 SECONDS
setInterval(

    checkRideStatus,

    2000

);