$(document).ready( function(){
    function select_proper_transmitters(satellite) {
        $('#transmitter-selection').prop('disabled', false);
        $('#transmitter-selection option').hide();
        $('#transmitter-selection option[data-satellite="' + satellite + '"]').show().prop('selected', true);

        $('.tle').hide();
        $('.tle[data-norad="' + satellite + '"]').show();
    }

    var satellite;

    var obs_filter = $('#form-obs').data('obs-filter');

    if (obs_filter) {
        satellite = $('input[name="satellite"]').val();
    } else {
        var minstart = $('#datetimepicker-start').data('date-minstart');
        var minend = $('#datetimepicker-end').data('date-minend');
        var maxrange = $('#datetimepicker-end').data('date-maxrange');
        $('#datetimepicker-start').datetimepicker();
        $('#datetimepicker-start').data('DateTimePicker').minDate(moment.utc().add(minstart, 'm'));
        $('#datetimepicker-end').datetimepicker();
        $('#datetimepicker-end').data('DateTimePicker').minDate(moment.utc().add(minend, 'm'));
        $("#datetimepicker-start").on('dp.change',function (e) {
            // Setting default, minimum and maximum for end
            $('#datetimepicker-end').data('DateTimePicker').defaultDate(moment.utc(e.date).add(60, 'm'));
            $('#datetimepicker-end').data('DateTimePicker').minDate(e.date);
            $('#datetimepicker-end').data('DateTimePicker').maxDate(moment.utc(e.date).add(maxrange, 'm'));
        });

        satellite = $('#satellite-selection').val();
    }

    select_proper_transmitters(satellite);

    $('#satellite-selection').bind('keyup change', function() {
        satellite = $(this).find(':selected').data('norad');
        select_proper_transmitters(satellite);
    });

    $('#calculate-observation').click( function(){
        $('.calculation-result').show();
        $('#timeline').empty();
        $('#hoverRes').hide();
        $('#windows-data').empty();
        var start_time = $('#datetimepicker-start input').val();
        var end_time = $('#datetimepicker-end input').val();

        $.ajax({
            url: '/prediction_windows/' + satellite + '/' + start_time + '/' + end_time + '/',
            beforeSend: function() { $('#loading').show(); }
        }).done(function(data) {
            $('#loading').hide();
            if (data.error) {
                var error_msg = data.error;
                console.log(data.error);
                $('#windows-data').html('<span class="text-danger">' + error_msg + '</span>');
            } else {
                var dc = 0; // Data counter
                var suggested_data = [];
                $('#windows-data').empty();
                $.each(data, function(i, k){
                    label = k.id + ' - ' + k.name;
                    var times = [];
                    $.each(k.window, function(m, n){
                        var starting_time = moment.utc(n.start).valueOf();
                        var ending_time = moment.utc(n.end).valueOf();
                        $('#windows-data').append('<input type="hidden" name="' + dc + '-starting_time" value="' + n.start + '">');
                        $('#windows-data').append('<input type="hidden" name="' + dc + '-ending_time" value="' + n.end + '">');
                        $('#windows-data').append('<input type="hidden" name="' + dc + '-station" value="' + k.id + '">');
                        times.push({starting_time: starting_time, ending_time: ending_time});
                        dc = dc + 1;
                    });
                    suggested_data.push({label: label, times: times});
                });

                $('#windows-data').append('<input type="hidden" name="total" value="' + dc + '">');
                if (dc > 0) {
                    timeline_init(start_time, end_time, suggested_data);
                } else {
                    var empty_msg = 'No Ground Station available for this observation window';
                    $('#windows-data').html('<span class="text-danger">' + empty_msg + '</span>');
                }
            }
        });
    });

    function timeline_init(start, end, payload){
        var start_time_timeline = moment.utc(start).valueOf();
        var end_time_timeline = moment.utc(end).valueOf();

        $('#timeline').empty();
        $('.coloredDiv').css('background-color', 'transparent');
        $('#name').empty();

        var chart = d3.timeline()
                      .beginning(start_time_timeline)
                      .ending(end_time_timeline)
                      .hover(function (d, i, datum) {
                          var div = $('#hoverRes');
                          var colors = chart.colors();
                          div.find('.coloredDiv').css('background-color', colors(i));
                          div.find('#name').text(datum.label);
                      })
                      .margin({left:140, right:10, top:0, bottom:50})
                      .tickFormat({format: d3.time.format.utc('%H:%M'), tickTime: d3.time.minutes, tickInterval: 30, tickSize: 6})
                      .stack();

        var svg_width = 1140;
        if (screen.width < 1200) { svg_width = 940; }
        if (screen.width < 992) { svg_width = 720; }
        if (screen.width < 768) { svg_width = screen.width - 30; }
        var svg = d3.select('#timeline').append('svg').attr('width', svg_width)
                    .datum(payload).call(chart);

        $('#hoverRes').show();
        $('#schedule-observation').removeAttr('disabled');
    }
});
