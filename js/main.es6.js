function tileHtml(title, subtitle) {
    var html = `
      <div class="tile is-parent">
      <article class="tile is-child box">
        <div class="content">
         <p class="title">${title}</p>
         <p class="subtitle">${subtitle}</p>
        </div>
      </article>
      </div>`
    
    return html
}
    
var coords = {}

if (navigator.geolocation) {
    coords.source = 'browser'
    navigator.geolocation.getCurrentPosition(showPosition);
} else { 
    coords.source = 'ip'
    $.get("/data", render);
}

function render(res) {
    var data = JSON.parse(res)
    $(".tile-area").append(tileHtml(data.county.name, data.county.population));
    if (data.place) {
	$(".tile-area").append(tileHtml(data.place.name, data.place.population));
    }
    if (data.tract) {
	$(".tile-area").append(tileHtml(data.tract.name, data.tract.population));
    }
}

function showPosition(position) {
    coords.lat = position.coords.latitude; 
    coords.lon = position.coords.longitude;
    $(".tile-area").append(tileHtml(coords.lat, coords.lon));

    $.get("/data", {
	lat: coords.lat,
	lon: coords.lon
    }, render);
}
