var expandIcon = 'm22,0c-12.2,0-22,9.8-22,22s9.8,22 22,22 22-9.8 22-22-9.8-22-22-22zm-1.3,19.3l-1.4,1.4c-0.4,0.4-1,0.4-1.4,0l-4-4c-0.3-0.3-0.9-0.1-0.9,0.4v1c0,0.6-0.4,1-1,1h-2c-0.6,0-1-0.4-1-1v-8c0-0.6 0.4-1 1-1h8c0.6,0 1,0.4 1,1v2c0,0.6-0.4,1-1,1h-1c-0.4,0-0.7,0.5-0.4,0.9l4,4c0.5,0.3 0.5,0.9 0.1,1.3zm14.3,14.7c0,0.6-0.4,1-1,1h-8c-0.6,0-1-0.4-1-1v-2c0-0.6 0.4-1 1-1h1c0.4,0 0.7-0.5 0.4-0.9l-4-4c-0.4-0.4-0.4-1 0-1.4l1.4-1.4c0.4-0.4 1-0.4 1.4,0l4,4c0.3,0.3 0.9,0.1 0.9-0.4v-1c0-0.6 0.4-1 1-1h2c0.6,0 1,0.4 1,1v8.1h-0.1z'

var margin = {
    top: 20,
    right: 20,
    bottom: 30,
    left: 50
}

function getData() {
    var url = '/data'
    return $.get(url)
}

function getSvg(selector) {
    var $container = $(selector)
    if ($container.has('svg').length) {
        //TODO
    } else {
        var svg = d3.select(selector).append('svg')
        svg.attr('height', $container.height())
        svg.attr('width', $container.width())
        svg.width = $container.width() - margin.left - margin.right
        svg.height = $container.height() - margin.top - margin.bottom

        svg.g = svg.append('g')
        svg.g.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')

        return svg;
    }
}

function maximizeChart(svg) {
    //TODO
}

function drawToolbar(svg) {
    var g = svg.g
    var path = g.append('path')
    path.attr('class', 'expand-button')
    var top = 0
    var left = svg.width*2 - margin.right
    path.attr('transform', 'scale(0.5), translate(' + left + ',' + top + ')')
    path.attr('d', expandIcon)
    path.on('click', (e) => {
        maximizeChart(svg)
    })
}

// line chart: https://bl.ocks.org/mbostock/3883245
function drawLineChart(data, selector) {
    var svg = getSvg(selector)
    drawToolbar(svg)
    var g = svg.g
    var width = svg.width
    var height = svg.height

    var x = d3.scaleTime()
        .rangeRound([0, width]);

    var y = d3.scaleLinear()
        .rangeRound([height, 0]);

    var line = d3.line()
        .x(function(d) { return x(new Date(d.date)) })
        .y(function(d) { return y(d.close) })

    x.domain(d3.extent(data.data, function(d) { return new Date(d.date) }))
    y.domain(d3.extent(data.data, function(d) { return d.close }))

    g.append("g")
        .attr("class", "axis axis--x")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x));

    g.append("g")
        .attr("class", "axis axis--y")
        .call(d3.axisLeft(y))
        .append("text")
        .attr("fill", "#fff")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", "0.71em")
        .style("text-anchor", "end")
        .text("Price (USD)");

    g.append("path")
        .datum(data.data)
        .attr("class", "line")
        .attr("d", line);
}

function drawChart(selector) {
    getData().done((data) => {
        drawLineChart(JSON.parse(data), selector)
    })
}
