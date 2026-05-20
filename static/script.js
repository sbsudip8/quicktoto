// MAP VARIABLES
let map;

let pickupLocation = null;
let dropLocation = null;

let pickupMarker = null;
let dropMarker = null;

let routingControl = null;

let driverMarkers = [];




// DRIVER ICON
const driverIcon = L.icon({

    iconUrl:

        "https://cdn-icons-png.flaticon.com/512/744/744465.png",

    iconSize: [35, 35],

    iconAnchor: [17, 35]

});




// PICKUP ICON
const pickupIcon = L.icon({

    iconUrl:

        "https://cdn-icons-png.flaticon.com/512/684/684908.png",

    iconSize: [35, 35],

    iconAnchor: [17, 35]

});




// DROP ICON
const dropIcon = L.icon({

    iconUrl:

        "https://cdn-icons-png.flaticon.com/512/2776/2776067.png",

    iconSize: [35, 35],

    iconAnchor: [17, 35]

});




// INITIALIZE MAP
map = L.map(

    "map"

).setView(

    [26.7271, 88.3953],

    13

);




// TILE LAYER
L.tileLayer(

    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",

    {

        attribution:

            "&copy; OpenStreetMap contributors"

    }

).addTo(map);




// PICKUP SEARCH FUNCTION
async function searchPickup() {

    let location = document.getElementById(

        "pickupSearch"

    ).value;




    if (!location) {

        return;

    }




    let response = await fetch(

        `https://nominatim.openstreetmap.org/search?format=json&q=${location}`

    );



    let data = await response.json();




    if (data.length > 0) {

        pickupLocation = {

            lat: parseFloat(data[0].lat),

            lng: parseFloat(data[0].lon)

        };




        // REMOVE OLD PICKUP
        if (pickupMarker) {

            map.removeLayer(

                pickupMarker

            );

        }




        // NEW PICKUP MARKER
        pickupMarker = L.marker(

            [

                pickupLocation.lat,

                pickupLocation.lng

            ],

            {

                icon: pickupIcon

            }

        )

        .addTo(map)

        .bindPopup(

            "📍 Pickup Location"

        )

        .openPopup();




        // UPDATE UI
        document.getElementById(

            "pickupText"

        ).innerText = location;




        // MOVE MAP
        map.setView(

            [

                pickupLocation.lat,

                pickupLocation.lng

            ],

            15

        );




        // DRAW ROUTE
        if (dropLocation) {

            drawRoute();

            updateFare();

        }

    }

    else {

        alert(

            "Location not found"

        );

    }

}




// DROP SEARCH FUNCTION
async function searchDrop() {

    let location = document.getElementById(

        "dropSearch"

    ).value;




    if (!location) {

        return;

    }




    let response = await fetch(

        `https://nominatim.openstreetmap.org/search?format=json&q=${location}`

    );



    let data = await response.json();




    if (data.length > 0) {

        dropLocation = {

            lat: parseFloat(data[0].lat),

            lng: parseFloat(data[0].lon)

        };




        // REMOVE OLD DROP
        if (dropMarker) {

            map.removeLayer(

                dropMarker

            );

        }




        // NEW DROP MARKER
        dropMarker = L.marker(

            [

                dropLocation.lat,

                dropLocation.lng

            ],

            {

                icon: dropIcon

            }

        )

        .addTo(map)

        .bindPopup(

            "🏁 Drop Location"

        )

        .openPopup();




        // UPDATE UI
        document.getElementById(

            "dropText"

        ).innerText = location;




        // DRAW ROUTE
        if (pickupLocation) {

            drawRoute();

            updateFare();

        }

    }

    else {

        alert(

            "Location not found"

        );

    }

}




// PICKUP SEARCH BUTTON
document.getElementById(

    "pickupSearchBtn"

).onclick = searchPickup;




// DROP SEARCH BUTTON
document.getElementById(

    "dropSearchBtn"

).onclick = searchDrop;




// ENTER KEY FOR PICKUP
document.getElementById(

    "pickupSearch"

).addEventListener(

    "keypress",

    function(e) {

        if (e.key === "Enter") {

            searchPickup();

        }

    }

);




// ENTER KEY FOR DROP
document.getElementById(

    "dropSearch"

).addEventListener(

    "keypress",

    function(e) {

        if (e.key === "Enter") {

            searchDrop();

        }

    }

);




// GPS BUTTON
document.getElementById(

    "gpsBtn"

).onclick = () => {

    navigator.geolocation.getCurrentPosition(

        position => {

            let lat = position.coords.latitude;

            let lng = position.coords.longitude;




            // SAVE PICKUP
            pickupLocation = {

                lat: lat,

                lng: lng

            };




            // REMOVE OLD PICKUP
            if (pickupMarker) {

                map.removeLayer(

                    pickupMarker

                );

            }




            // PICKUP MARKER
            pickupMarker = L.marker(

                [

                    lat,

                    lng

                ],

                {

                    icon: pickupIcon

                }

            )

            .addTo(map)

            .bindPopup(

                "📍 You are here"

            )

            .openPopup();




            // UPDATE UI
            document.getElementById(

                "pickupText"

            ).innerText =

                lat.toFixed(5) +

                ", " +

                lng.toFixed(5);




            // MOVE MAP
            map.setView(

                [lat, lng],

                15

            );




            // DRAW ROUTE
            if (dropLocation) {

                drawRoute();

                updateFare();

            }

        }

    );

};




// CLICK MAP TO SET DROP
map.on(

    "click",

    function(e) {

        // REMOVE OLD DROP
        if (dropMarker) {

            map.removeLayer(

                dropMarker

            );

        }




        // SAVE LOCATION
        dropLocation = {

            lat: e.latlng.lat,

            lng: e.latlng.lng

        };




        // DROP MARKER
        dropMarker = L.marker(

            [

                dropLocation.lat,

                dropLocation.lng

            ],

            {

                icon: dropIcon

            }

        )

        .addTo(map)

        .bindPopup(

            "🏁 Drop Location"

        )

        .openPopup();




        // UPDATE UI
        document.getElementById(

            "dropText"

        ).innerText =

            dropLocation.lat.toFixed(5) +

            ", " +

            dropLocation.lng.toFixed(5);




        // DRAW ROUTE
        if (pickupLocation) {

            drawRoute();

            updateFare();

        }

    }

);




// DRAW ROUTE
function drawRoute() {

    // REMOVE OLD ROUTE
    if (routingControl) {

        map.removeControl(

            routingControl

        );

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
function calculateDistance(

    lat1,
    lng1,
    lat2,
    lng2

) {

    let dx = lat1 - lat2;
    let dy = lng1 - lng2;

    return Math.sqrt(

        dx * dx + dy * dy

    );

}




// UPDATE FARE
function updateFare() {

    if (

        !pickupLocation ||

        !dropLocation

    ) {

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




    fare = Math.round(

        fare

    );




    document.getElementById(

        "fareText"

    ).innerText = "₹" + fare;

}




// UPDATE FARE ON TYPE CHANGE
document.querySelectorAll(

    'input[name="rideType"]'

).forEach(radio => {

    radio.addEventListener(

        "change",

        updateFare

    );

});




// REQUEST BUTTON
let requestBtn = document.getElementById(

    "requestBtn"

);




// REQUEST RIDE
requestBtn.onclick = async () => {

    if (

        !pickupLocation ||

        !dropLocation

    ) {

        alert(

            "Please set pickup and drop locations"

        );



        return;

    }




    let rideType = document.querySelector(

        'input[name="rideType"]:checked'

    ).value;




    let seatCount = document.getElementById(

        "seatCount"

    ).value;




    let response = await fetch(

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

                ).innerText,

                seats: seatCount

            })

        }

    );




    let data = await response.json();




    // SAVE BOOKING ID
    localStorage.setItem(

        "booking_id",

        data.booking_id

    );




    alert(

        "🔍 Searching for Toto Driver..."

    );

};




// LIVE STATUS
let lastStatus = "";




// CHECK BOOKING STATUS
async function checkBookingStatus() {

    let booking_id = localStorage.getItem(

        "booking_id"

    );




    // NO ACTIVE BOOKING
    if (!booking_id) {

        return;

    }




    let response = await fetch(

        `/booking_status/${booking_id}`

    );



    let data = await response.json();




    // STATUS CHANGED
    if (data.status !== lastStatus) {

        if (data.status === "accepted") {

            alert(

                "✅ Ride Accepted"

            );

        }




        if (data.status === "rejected") {

            alert(

                "❌ Ride Rejected"

            );

        }




        if (data.status === "arrived") {

            alert(

                "📍 Driver Arrived"

            );

        }




        if (data.status === "onboard") {

            alert(

                "👤 Passenger Onboard"

            );

        }




        if (data.status === "completed") {

            alert(

                "✅ Ride Completed"

            );



            localStorage.removeItem(

                "booking_id"

            );

        }




        lastStatus = data.status;

    }

}




// ONLINE DRIVERS
async function loadOnlineDrivers() {

    if (!map) {

        return;

    }




    // REMOVE OLD MARKERS
    driverMarkers.forEach(marker => {

        map.removeLayer(

            marker

        );

    });




    driverMarkers = [];




    // FETCH DRIVERS
    let response = await fetch(

        "/get_online_drivers"

    );



    let drivers = await response.json();




    drivers.forEach(driver => {

        // SKIP EMPTY GPS
        if (

            driver.latitude === 0 ||

            driver.longitude === 0

        ) {

            return;

        }




        let marker = L.marker(

            [

                driver.latitude,

                driver.longitude

            ],

            {

                icon: driverIcon

            }

        )

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




// LOAD ONLINE DRIVERS
loadOnlineDrivers();




// REFRESH DRIVER LOCATIONS
setInterval(

    loadOnlineDrivers,

    5000

);




// CHECK BOOKING STATUS
setInterval(

    checkBookingStatus,

    2000

);