const toggleBtn = document.getElementById(

    "toggleBtn"

);

let isOnline = false;




// TOGGLE ONLINE/OFFLINE
toggleBtn.onclick = async () => {

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

        // START GPS
        startDriverGPS();




        // UPDATE STATUS
        document.getElementById(

            "availabilityText"

        ).innerText =

            "Status: Online";



        toggleBtn.innerText =

            "🔴 Go Offline";




        // WAITING UI
        document.getElementById(

            "rideContainer"

        ).innerHTML = `

            <h3>

                Waiting for Ride...

            </h3>

        `;




        // CHECK RIDES IMMEDIATELY
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




        // OFFLINE UI
        document.getElementById(

            "rideContainer"

        ).innerHTML = `

            <h3>

                🔴 You are offline

            </h3>

        `;

    }

};




// DRIVER GPS
function startDriverGPS() {

    navigator.geolocation.watchPosition(

        async position => {

            let lat = position.coords.latitude;

            let lng = position.coords.longitude;




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

    // ONLY ONLINE DRIVERS
    if (!isOnline) {

        return;

    }



    let response = await fetch(

        "/get_ride"

    );



    let data = await response.json();




    // IF RIDE EXISTS
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



            <button id="acceptBtn">

                ✅ Accept Ride

            </button>



            <button id="rejectBtn">

                ❌ Reject Ride

            </button>

        `;




        // ACCEPT BUTTON
        document.getElementById(

            "acceptBtn"

        ).onclick = async () => {

            await fetch(

                "/accept_ride",

                {

                    method: "POST"

                }

            );



            // UPDATE DRIVER UI
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

                        method: "POST"

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

                        method: "POST"

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

                        method: "POST"

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

            };

        };




        // REJECT BUTTON
        document.getElementById(

            "rejectBtn"

        ).onclick = async () => {

            await fetch(

                "/reject_ride",

                {

                    method: "POST"

                }

            );



            alert(

                "❌ Ride Rejected"

            );

        };

    }




    // NO RIDE FOUND
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




// CHECK RIDES EVERY 2 SECONDS
setInterval(

    fetchRide,

    2000

);