$( ".list-group-item a" ).on( "click", function(event) {
    event.preventDefault();

    $.ajax({
        url : ".",
        type : "GET",
        data : { 'room': $(this).attr('data-pk') },

        // Handle success response
        success : function(json) {
            console.log(json);
        },

        // Unsuccessfull response
        error : function(xhr,errmsg,err) {
            
        }
    });
});