
$(function () {

    var datasets = ${datasets | n};

    // hard-code color indices to prevent them from shifting as
    // countries are turned on/off
    //var i = 0;
    //$.each(datasets, function(key, val) {
    //    val.color = i;
    //    ++i;
    //});
    
    // insert checkboxes 
    var choiceContainer = $("#choices");
    choiceContainer.append('<form class="form form-horizontal">');
    $.each(datasets, function(key, val) {
        choiceContainer.append('<input type="checkbox" name="' + key +
                               '" checked="checked" id="id' + key + '" />' +
                               '<label for="id' + key + '">'
                                + val.label + '</label>');
    });
    choiceContainer.append('</form>');
    choiceContainer.find("input").click(plotAccordingToChoices);

    
    var last_ranges = null;

    function plotAccordingToChoices( ranges ) {
        var data = [];

        choiceContainer.find("input:checked").each(function () {
            var key = $(this).attr("name");
            if (key && datasets[key])
                data.push(datasets[key]);
        });

        if (ranges == null || ranges.yaxis == null) {
            xmin = 0;
            xmax = null;
            ymin = 0;
            ymax = null;
        } else {
            ymin = ranges.yaxis.from;
            ymax = ranges.yaxis.to;
            xmin = ranges.xaxis.from;
            xmax = ranges.xaxis.to;
        }

        if (data.length > 0)
            $.plot($("#placeholder"), data, {
                yaxis: { min: ymin, max: ymax },
                xaxis: { tickDecimals: 0, min: xmin, max: xmax },
                series: { lines: { lineWidth: 1 }, shadowSize: 0 },
                selection: { mode: "xy" }
            });
    }

    $("#placeholder").bind("plotselected", function (event, ranges) {
        // clamp the zooming to prevent eternal zoom
        if (ranges.xaxis.to - ranges.xaxis.from < 0.00001)
            ranges.xaxis.to = ranges.xaxis.from + 0.00001;
        if (ranges.yaxis.to - ranges.yaxis.from < 0.00001)
            ranges.yaxis.to = ranges.yaxis.from + 0.00001;
        
        // do the zooming
        plotAccordingToChoices( ranges );

    });

    plotAccordingToChoices();
});
