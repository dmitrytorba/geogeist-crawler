var x = document.getElementById("demo");

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition);
    } else { 
        x.innerHTML = "Geolocation is not supported by this browser.";
    }
}

function render(data) {
    $("#demo").html(data);
}

function showPosition(position) {
    var lat = position.coords.latitude; 
    var lon = position.coords.longitude;
    x.innerHTML = "Latitude: " + lat + 
	"<br>Longitude: " + lon; 

    $.get("/data", {
	lat: lat,
	lon: lon
    }, render);
}
