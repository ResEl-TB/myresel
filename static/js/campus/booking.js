// Check if the room is valid before sending the booking

var roomChoices = document.getElementsByClassName("room-choice");

function checkAvailability(form){
    var start = document.getElementById("startDate").value;
    var end = document.getElementById("endDate").value;
    var submit = document.getElementById("booking-submit");
    var send = true;
    submitText = submit.innerHTML; //avoid issues with translation stuff
    submit.innerHTML = '<span class="fa fa-spinner fa-pulse"></span>';
    for(var i=0; i<roomChoices.length; i++){
        if(roomChoices[i].selected){
            $.ajax({
                url : checkFormURL, // /!\ Needs to be defined in the html page /!\
                type : "GET",
                async: false,
                data : {"value": roomChoices[i].value, "start": start, "end": end, /* {% if booking %}"id":  {{booking}}  {% endif %} */},// atm let's take care of the creation
                success : function(data){
                    if(data != "0"){
                        answer = confirm(
                            "ATTENTION:\n"+
                            "La salle \"" + data +
                            "\" est déjà réservée sur ce créneau.\n"+
                            "Assurez-vous que les activités sont compatibles.\n\n"+
                            "Pour confirmer, cliquez sur OK"
                        );
                        if(!answer){send=false;};
                    }
                },
            });
        };
    };
    if (send){
        //form.submit();
        validateAndSend();
    }
    submit.innerHTML = submitText;
}

/*
Send the form to check if its is valid and show errors if invalid or
reload the page if valid
*/

function validateAndSend() {
    var form = $('#booking-form');
    $.ajax({
        url : sendFormURL, // /!\ Needs to be defined in the html page /!\
        type : "POST",
        async : false,
        data : form.serialize(),
        success : function(data){
             location.reload();
        },
        error : function(data){
            var errors = document.getElementById("booking-errors");
            errors.style.display = 'block';
            errors.innerHTML = data.responseJSON.errors;
        }
    });
}

// Auto fill the endDate input when selecting the startDate

var startDateInput = document.getElementById("startDate");
var endDateInput = document.getElementById("endDate");

function addEndDate(){
    if (!endDateInput.value){
        endDateInput.value = startDateInput.value;
    }
};

jQuery.datetimepicker.setLocale( "{{ request.LANGUAGE_CODE }}" );
$( ".datetimepicker" ).datetimepicker({
    format: 'Y-m-d H:i:00',
});
