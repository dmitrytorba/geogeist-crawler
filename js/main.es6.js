function censusTileHtml(conf) {
    var html = `
      <div class="tile is-parent">
      <article class="tile is-child box">
        <div class="content">
         <p class="title">${conf.title}</p>
         <p class="subtitle">Population: ${conf.population}</p>
         <p class="subtitle">Houses: ${conf.houses}</p>
        </div>
      </article>
      </div>`
    
    return html
}

function coordTileHtml(conf) {
    var html = `
      <div class="tile is-parent">
      <article class="tile is-child box">
        <div class="content">
         <p class="subtitle">Coordinates: ${conf.lat}, ${conf.lon}</p>
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

function renderCounty(data) {
    var title = data.county.name + ' County'
    var html = censusTileHtml({
	'title': title,
	'population': data.county.population.total,
	'houses': data.county.houses
    })
    $(".tile-area").append(html)
}

function renderPlace(data) {
    if (data.place) {
	var html = censusTileHtml({
	    'title': data.place.name,
	    'population': data.place.population.total,
	    'houses': data.place.houses
	})
	$('.tile-area').append(html)
    }
}

function renderTract(data) {
    if (data.tract) {
	var title = 'Tract # ' + data.tract.name
	var html = censusTileHtml({
	    'title': title,
	    'population': data.tract.population.total,
	    'houses': data.tract.houses
	})
	$('.tile-area').append(html)
    }
}

function render(res) {
    var data = JSON.parse(res)
    renderCounty(data)
    renderPlace(data)
    renderTract(data)
}

function showPosition(position) {
    coords.lat = position.coords.latitude; 
    coords.lon = position.coords.longitude;
    var html = coordTileHtml(coords)
    $(".tile-area").append(html)

    $.get("/data", {
	lat: coords.lat,
	lon: coords.lon
    }, render);
}
