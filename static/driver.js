// DRIVER STATE
let isOnline = false;

let rideAccepted = false;




// BUTTON
let toggleBtn;




// DRIVER MAP
let driverMap;

let passengerMarker = null;

let routeControl = null;

let driverMarker = null;




// DRIVER GPS
let currentDriverLat = null;

let currentDriverLng = null;




// DRIVER ICON
const driverIcon = L.icon({

    iconUrl:

        "https://cdn-icons-png.flaticon.com/512/744/744465.png",

    iconSize: [35, 35],

    iconAnchor: [17, 35]

});




// PASSENGER ICON
const passengerIcon = L.icon({

    iconUrl:

        "https://cdn-icons-png.flaticon.com/512/684/684908.png",

    iconSize: [35, 35],

    iconAnchor: [17, 35]

});




document.addEventListener(

    "DOMContentLoaded",

    () => {

        // BUTTON
        toggleBtn = document.getElementById(

            "toggleBtn"

        );




        console.log(

            "Toggle button loaded"

        );




        // INITIALIZE DRIVER MAP
        driverMap = L.map(

            "driverMap"

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

        ).addTo(driverMap);




        // TOGGLE BUTTON
        toggleBtn.addEventListener(

            "click",

            async () => {

                console.log(

                    "Button clicked"

                );




                // TOGGLE STATE
                isOnline = !isOnline;




                // SEND TO BACKEND
                await fetch(

                    "/toggle_driver_status",

                    {

                        method: "POST",

                        headers: {

                            "Content-Type": "application/json"

                        },

                        body: JSON.stringify({

                            online: isOnline

                        })

                    }

                );




                // ONLINE
                if (isOnline) {

                    startDriverGPS();




                    document.getElementById(

                        "availabilityText"

                    ).innerText =

                        "Status: Online";




                    toggleBtn.innerText =

                        "🔴 Go Offline";




                    document.getElementById(

                        "rideContainer"

                    ).innerHTML = `

                        <h3>

                            Waiting for Ride...

                        </h3>

                    `;




                    fetchRide();

                }




                // OFFLINE
                else {

                    document.getElementById(

                        "availabilityText"

                    ).innerText =

                        "Status: Offline";




                    toggleBtn.innerText =

                        "🟢 Go Online";




                    document.getElementById(

                        "rideContainer"

                    ).innerHTML = `

                        <h3>

                            🔴 You are offline

                        </h3>

                    `;

                }

            }

        );

    }

);




// DRIVER GPS
function startDriverGPS() {

    navigator.geolocation.watchPosition(

        async position => {

            let lat = position.coords.latitude;

            let lng = position.coords.longitude;




            // SAVE DRIVER LOCATION
            currentDriverLat = lat;

            currentDriverLng = lng;




            // REMOVE OLD DRIVER MARKER
            if (driverMarker) {

                driverMap.removeLayer(

                    driverMarker

                );

            }




            // DRIVER MARKER
            driverMarker = L.marker(

                [

                    lat,

                    lng

                ],

                {

                    icon: driverIcon

                }

            )

            .addTo(driverMap)

            .bindPopup(

                "🚖 Your Location"

            );




            // MOVE MAP
            driverMap.setView(

                [

                    lat,

                    lng

                ],

                14

            );




            // SEND GPS TO BACKEND
            await fetch(

                "/update_driver_location",

                {

                    method: "POST",

                    headers: {

                        "Content-Type": "application/json"

                    },

                    body: JSON.stringify({

                        latitude: lat,

                        longitude: lng

                    })

                }

            );

        }

    );

}




// FETCH RIDES
async function fetchRide() {

    // ONLY ONLINE
    if (!isOnline) {

        return;

    }




    // ACTIVE RIDE
    if (rideAccepted) {

        return;

    }




    let response = await fetch(

        "/get_ride"

    );



    let data = await response.json();




    // RIDE EXISTS
    if (data.ride) {

        document.getElementById(

            "rideContainer"

        ).innerHTML = `

            <h2>

                Incoming Ride

            </h2>



            <p>

                <strong>Ride Type:</strong>

                ${data.ride.rideType}

            </p>



            <p>

                <strong>Fare:</strong>

                ${data.ride.fare}

            </p>



            <p>

                <strong>Seats:</strong>

                ${data.ride.seats}

            </p>



            <button id="acceptBtn">

                ✅ Accept Ride

            </button>



            <button id="rejectBtn">

                ❌ Reject Ride

            </button>

        `;




        // PASSENGER PICKUP
        let pickup = data.ride.pickup;




        // REMOVE OLD PASSENGER MARKER
        if (passengerMarker) {

            driverMap.removeLayer(

                passengerMarker

            );

        }




        // PASSENGER MARKER
        passengerMarker = L.marker(

            [

                pickup.lat,

                pickup.lng

            ],

            {

                icon: passengerIcon

            }

        )

        .addTo(driverMap)

        .bindPopup(

            "📍 Passenger Pickup"

        )

        .openPopup();




        // REMOVE OLD ROUTE
        if (routeControl) {

            driverMap.removeControl(

                routeControl

            );

        }




        // DRAW ROUTE
        if (

            currentDriverLat &&

            currentDriverLng

        ) {

            routeControl = L.Routing.control({

                waypoints: [

                    L.latLng(

                        currentDriverLat,

                        currentDriverLng

                    ),

                    L.latLng(

                        pickup.lat,

                        pickup.lng

                    )

                ],




                lineOptions: {

                    styles: [

                        {

                            color: "blue",

                            opacity: 0.8,

                            weight: 6

                        }

                    ]

                },




                routeWhileDragging: false,

                draggableWaypoints: false,

                addWaypoints: false,

                fitSelectedRoutes: true,

                show: false,

                createMarker: () => null

            }).addTo(driverMap);

        }




        // MOVE MAP
        driverMap.setView(

            [

                pickup.lat,

                pickup.lng

            ],

            14

        );




        // ACCEPT BUTTON
        document.getElementById(

            "acceptBtn"

        ).onclick = async () => {

            let response = await fetch(

                "/accept_ride",

                {

                    method: "POST",

                    headers: {

                        "Content-Type": "application/json"

                    },

                    body: JSON.stringify({

                        booking_id: data.ride.booking_id

                    })

                }

            );



            let result = await response.json();




            // ALREADY TAKEN
            if (

                result.status ===

                "Already Taken"

            ) {

                alert(

                    "Ride already accepted by another driver."

                );



                return;

            }




            // LOCK CURRENT RIDE
            rideAccepted = true;




            // UPDATE UI
            document.getElementById(

                "rideContainer"

            ).innerHTML = `

                <h2>

                    Ride Accepted

                </h2>



                <button id="arrivedBtn">

                    📍 Reached Pickup

                </button>



                <button id="onboardBtn">

                    👤 Passenger Onboard

                </button>



                <button id="completeBtn">

                    ✅ Complete Ride

                </button>

            `;




            // ARRIVED
            document.getElementById(

                "arrivedBtn"

            ).onclick = async () => {

                await fetch(

                    "/ride_arrived",

                    {

                        method: "POST",

                        headers: {

                            "Content-Type": "application/json"

                        },

                        body: JSON.stringify({

                            booking_id: data.ride.booking_id

                        })

                    }

                );



                alert(

                    "Reached Pickup"

                );

            };




            // ONBOARD
            document.getElementById(

                "onboardBtn"

            ).onclick = async () => {

                await fetch(

                    "/ride_onboard",

                    {

                        method: "POST",

                        headers: {

                            "Content-Type": "application/json"

                        },

                        body: JSON.stringify({

                            booking_id: data.ride.booking_id

                        })

                    }

                );



                alert(

                    "Passenger Onboard"

                );

            };




            // COMPLETE
            document.getElementById(

                "completeBtn"

            ).onclick = async () => {

                await fetch(

                    "/complete_ride",

                    {

                        method: "POST",

                        headers: {

                            "Content-Type": "application/json"

                        },

                        body: JSON.stringify({

                            booking_id: data.ride.booking_id

                        })

                    }

                );



                alert(

                    "Ride Completed"

                );




                // RESET UI
                document.getElementById(

                    "rideContainer"

                ).innerHTML = `

                    <h3>

                        Waiting for Ride...

                    </h3>

                `;




                // REMOVE ROUTE
                if (routeControl) {

                    driverMap.removeControl(

                        routeControl

                    );

                }




                // RESET STATE
                rideAccepted = false;

            };

        };




        // REJECT BUTTON
        document.getElementById(

            "rejectBtn"

        ).onclick = async () => {

            await fetch(

                "/reject_ride",

                {

                    method: "POST",

                    headers: {

                        "Content-Type": "application/json"

                    },

                    body: JSON.stringify({

                        booking_id: data.ride.booking_id

                    })

                }

            );



            alert(

                "❌ Ride Rejected"

            );




            // RESET UI
            document.getElementById(

                "rideContainer"

            ).innerHTML = `

                <h3>

                    Waiting for Ride...

                </h3>

            `;




            // REMOVE ROUTE
            if (routeControl) {

                driverMap.removeControl(

                    routeControl

                );

            }

        };

    }




    // NO RIDE
    else {

        document.getElementById(

            "rideContainer"

        ).innerHTML = `

            <h3>

                Waiting for Ride...

            </h3>

        `;

    }

}




// CHECK RIDES
window.onload = () => {

    // BUTTON
    toggleBtn = document.getElementById(

        "toggleBtn"

    );




    // INITIALIZE DRIVER MAP
    driverMap = L.map(

        "driverMap"

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

    ).addTo(driverMap);




    // START FETCH LOOP
    setInterval(

        fetchRide,

        2000

    );

};




// CHECK TIMEOUTS
setInterval(

    async () => {

        await fetch(

            "/check_timeout"

        );

    },

    5000

);