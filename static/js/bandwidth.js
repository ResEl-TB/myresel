/**
 * Convert to human readable
 * From: https://stackoverflow.com/a/14919494
 * @param bytes
 * @param si
 * @returns {string}
 */
function humanFileSize(bytes, si) {
    var thresh = si ? 1000 : 1024;
    if(Math.abs(bytes) < thresh) {
        return bytes + ' B';
    }
    var units = si
        ? ['ko','Mo','Go','To','Po','Eo','Zo','Yo']
        : ['Kio','Mio','Gio','Tio','Pio','Eio','Zio','Yio'];
    var u = -1;
    do {
        bytes /= thresh;
        ++u;
    } while(Math.abs(bytes) >= thresh && u < units.length - 1);
    return bytes.toFixed(1)+' '+units[u];
}

var ctx = document.getElementById("bandwidthChart");
var myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],

        datasets: [{
            label: 'Téléchargements',
            data: [],
            borderColor: 'rgba(45, 115, 160, .6)',
            backgroundColor: 'rgba(45, 115, 160, .4)',
            pointRadius: 1

        },
            {
                label: 'Téléversements',
                data: [],
                borderColor: 'rgba(192, 0, 26, .6)',
                backgroundColor: 'rgba(192, 0, 26, .4)',
                pointRadius: 1

            }]
    },
    options: {
        scales: {
            yAxes: [{
                ticks: {
                    beginAtZero:true,
                    callback: function(value, index, values) {
                        return humanFileSize(value, true);
                    }
                }

            }],
            xAxes: [{
                ticks: {
                    callback: function(value, index, values) {
                        // return value;
                        return new Date(value*1000).toLocaleString();
                    }
                }

            }]
        }
    }
});

/*
 Date picker settings and hooks
 */

var date = new Date();
var start_date = date;
var date_diff = 7;
var end_date = (new Date(start_date));
end_date.setDate(start_date.getDay() - date_diff);


var up_raw_data = [];
var down_raw_data = [];
var label_raw_data = [];

$("#end-date").val(start_date.toISOString().substr(0, 10));
$("#start-date").val(end_date.toISOString().substr(0, 10));


var update_graph = function(up, down, label){
    myChart.data.labels = label;
    myChart.data.datasets[0].data = down;
    myChart.data.datasets[1].data = up;
    myChart.update();
};

var cumul = function(arr) {
    var out = [];
    var curr = 0;
    for (var i = 0; i < arr.length ; i++) {
        n_curr = curr + arr[i];
        out.push(n_curr);
        curr = n_curr;
    }
    return out;
};

var download_data = function() {
    var start_date = $("#start-date").val();
    var end_date = $("#end-date").val();

    $.getJSON( "/machines/consomation", { s: start_date, e: end_date }, function( data ) {
        up_raw_data = data.up;
        down_raw_data = data.down;
        label_raw_data = data.labels;

        if ($('#cumulate-toogle input[name=instantorcumul]:checked').val() == "instant") {
            update_graph(up_raw_data, down_raw_data, label_raw_data);
        } else {
            update_graph(cumul(up_raw_data), cumul(down_raw_data), label_raw_data);
        }
    });
};

$('#bw-control .input-daterange').datepicker({
    format: "yyyy-mm-dd",
    maxViewMode: 1,
    autoclose: true,
    endDate: "0d",
    todayBtn: "linked",
    language: "fr",
    todayHighlight: true
}).on("changeDate", function(e) {
    download_data();
});

$('#cumulate-toogle input').on('change', function() {
    if ($('#cumulate-toogle input[name=instantorcumul]:checked').val() == "instant") {
        update_graph(up_raw_data, down_raw_data, label_raw_data);
    } else {
        update_graph(cumul(up_raw_data), cumul(down_raw_data), label_raw_data);
    }
});

download_data();