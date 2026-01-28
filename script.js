let map;
let pickupMarker;
let dropMarker;
let pickupLocation = null;
let dropLocation = null;

const gpsBtn = document.getElementById("gpsBtn");
const requestBtn = document.getElementById("requestBtn");

gpsBtn.onclick = () => {
  if (!navigator.geolocation) {
    alert("GPS not supported");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    position => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;

      pickupLocation = { lat, lng };
      document.getElementById("pickupText").innerText =
        lat.toFixed(5) + ", " + lng.toFixed(5);

      initMap(lat, lng);
    },
    () => alert("Location permission denied")
  );
};

function initMap(lat, lng) {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat, lng },
    zoom: 15
  });

  pickupMarker = new google.maps.Marker({
    position: { lat, lng },
    map: map,
    label: "P"
  });

  map.addListener("click", e => {
    if (dropMarker) dropMarker.setMap(null);

    dropLocation = {
      lat: e.latLng.lat(),
      lng: e.latLng.lng()
    };

    dropMarker = new google.maps.Marker({
      position: dropLocation,
      map: map,
      label: "D"
    });

    document.getElementById("dropText").innerText =
      dropLocation.lat.toFixed(5) + ", " +
      dropLocation.lng.toFixed(5);
  });
}

requestBtn.onclick = () => {
  if (!pickupLocation || !dropLocation) {
    alert("Please set pickup and drop locations");
    return;
  }

  alert(
    "Ride Requested!\n\nPickup: " +
    JSON.stringify(pickupLocation) +
    "\nDrop: " +
    JSON.stringify(dropLocation)
  );

  // Backend call will be added later
};
