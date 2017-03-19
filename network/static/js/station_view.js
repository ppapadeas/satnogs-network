/* global L */

$(document).ready(function() {
    'use strict';

    // Render Station success rate
    var success_rate = $('.progress-bar-success').data('success-rate');
    var percentagerest = $('.progress-bar-danger').data('percentagerest');
    $('.progress-bar-success').css('width', success_rate + '%');
    $('.progress-bar-danger').css('width', percentagerest + '%');

    // Reading data for station
    var station_info = $('#station-info').data();

    // Confirm station deletion
    var message = 'Do you really want to delete this Ground Station?';
    var actions = $('#station-delete');
    if (actions.length) {
        actions[0].addEventListener('click', function(e) {
            if (! confirm(message)) {
                e.preventDefault();
            }
        });
    }

    function drawPolarPlot (canvas, data) {
        var ctx = canvas.getContext('2d');
        var centerΧ = ctx.canvas.width / 2;
        var centerY = ctx.canvas.height / 2;
        var canvasSize = Math.min(ctx.canvas.width, ctx.canvas.height);
        var altUnit = canvasSize/(2.5 * 90);
        var fontRatio = 0.07;
        var radius;
        var radians;

        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        //Draw altitude circles
        ctx.beginPath();
        var altCircles = [90, 60, 30];
        for (var i=0; i < altCircles.length; i++) {
            radius = altCircles[i] * altUnit;
            ctx.moveTo(centerΧ + radius,centerY);
            for(var th=1;th<=360;th+=1) {
                radians = (Math.PI/180) * th;
                ctx.lineTo(centerΧ + radius * Math.cos(radians),centerY + radius * Math.sin(radians));
            }
        }

        ctx.strokeStyle = '#444444';
        ctx.lineWidth = 1;
        ctx.stroke();
        //Draw axis and letters
        radius = 96 * altUnit;
        ctx.moveTo(centerΧ, centerY);
        ctx.lineTo(centerΧ, centerY + radius);
        ctx.moveTo(centerΧ, centerY);
        ctx.lineTo(centerΧ, centerY-radius);
        ctx.moveTo(centerΧ, centerY);
        ctx.lineTo(centerΧ + radius, centerY);
        ctx.moveTo(centerΧ, centerY);
        ctx.lineTo(centerΧ-radius, centerY);

        radius = 98 * altUnit;
        ctx.font = (canvasSize * fontRatio) + 'px serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText('N', centerΧ, centerY - radius);
        ctx.textBaseline = 'top';
        ctx.fillText('S', centerΧ, centerY + radius);
        ctx.strokeStyle = '#000000';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText('W', centerΧ - radius, centerY);
        ctx.textAlign = 'left';
        ctx.fillText('E', centerΧ + radius, centerY);
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 1;
        ctx.stroke();

        //Draw data
        ctx.beginPath();
        radians = (Math.PI/180) * (data[0][1] - 90);
        radius = (90 - data[0][0]) * altUnit;
        ctx.moveTo(centerΧ + radius * Math.cos(radians),centerY + radius * Math.sin(radians));
        ctx.lineTo(centerΧ + radius * Math.cos(radians),centerY + radius * Math.sin(radians));


        var dataLength = data.length;
        for (var j=1; j< dataLength; j++) {
            radians = (Math.PI/180) * (data[j][1] - 90);
            radius = (90 - data[j][0] ) * altUnit;
            ctx.lineTo(centerΧ + radius * Math.cos(radians),centerY + radius * Math.sin(radians));
        }

        ctx.strokeStyle = '#0000FF';
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    $('canvas').each(function(){
        var $this = $(this);
        drawPolarPlot($this.get(0), $this.data().points);
    });

    // Init the map
    var mapboxid = $('div#map-station').data('mapboxid');
    var mapboxtoken = $('div#map-station').data('mapboxtoken');

    L.mapbox.accessToken = mapboxtoken;
    L.mapbox.config.FORCE_HTTPS = true;
    var map = L.mapbox.map('map-station', mapboxid,{
        zoomControl: false
    }).setView([station_info.lat, station_info.lng], 6);

    // Add a marker
    L.mapbox.featureLayer({
        type: 'Feature',
        geometry: {
            type: 'Point',
            coordinates: [
                parseFloat(station_info.lng),
                parseFloat(station_info.lat)
            ]
        },
        properties: {
            title: station_info.name,
            'marker-size': 'large',
            'marker-color': '#666',
        }
    }).addTo(map);

    // Filters
    $('#antenna-filter').submit(function () {
        var the_form = $(this);

        the_form.find('input[type="checkbox"]').each( function () {
            var the_checkbox = $(this);


            if( the_checkbox.is(':checked') === true ) {
                the_checkbox.attr('value','1');
            } else {
                the_checkbox.prop('checked',true);
                // Check the checkbox but change it's value to 0
                the_checkbox.attr('value','0');
            }
        });
    });

    $('.filter-section input[type=checkbox]').change(function() {
        $('#antenna-filter').submit();
    });
});
