function censusPlaceHtml(conf) {
    var html = `
      <article class="tile is-child">
        <div class="content">
         <p class="title">${conf.name}</p>
         <p class="subtitle">Population: ${conf.population}</p>
        </div>
      </article>`
    
    return html
}
    
var x = document.getElementById("demo");

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition);
    } else { 
        x.innerHTML = "Geolocation is not supported by this browser.";
    }
}

function render(res) {
    var data = JSON.parse(res)
    $("#demo").html(censusPlaceHtml({
	name: data.name,
	population: data.population
    }));
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
