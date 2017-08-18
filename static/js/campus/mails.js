// Get CSRF token
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$('tr').each(function() {
    var mailid = $(this).data('mailid');

    $(this).find('.moderate').confirm({
        columnClass: 'col-md-12',
        backgroundDismiss: true,
        type: 'green',
        title: 'Modérer le mail',
        content: function () {
            var self = this;
            return $.ajax({
                url: '/campus/mails/modérer/',
                data: {'id': mailid},
                method: 'GET'
            }).done( function (response) {
                self.setContent(
                    '<form action="">' +
                    
                    '<div class="form-group">' +
                    '<div class="input-group">' +
                    '<span class="input-group-addon"><i class="fa fa-fw fa-user"></i></span>' +
                    '<input type="text" name="sender" class="form-control" value="'+ response.sender +'" readonly="readonly">' +
                    '</div>' +
                    '</div>' +

                    '<div class="form-group">' +
                    '<div class="input-group">' +
                    '<span class="input-group-addon"><i class="fa fa-fw fa-envelope-o"></i></span>' +
                    '<input type="text" name="subject" class="form-control" value="'+ response.subject +'">' +
                    '</div>' +
                    '</div>' +

                    '<div class="form-group">' +
                    '<textarea class="form-control" name="content" style="resize: none;" rows="10">' +
                    response.content +
                    '</textarea>' +
                    '</div>' +

                    '</form>'
                );
            }).fail( function () {
                self.setContent('Something went wrong.');
            });
        },
        buttons: {
            formSubmit: {
                text: 'Modérer',
                btnClass: 'btn-green',
                action: function () {
                    $.ajax({
                        url: '/campus/mails/modérer/',
                        type: 'POST',
                        data: {
                            'id': mailid,
                            'sender': this.$content.find('input[name="sender"]').val(),
                            'subject': this.$content.find('input[name="subject"]').val(),
                            'content': this.$content.find('textarea[name="content"]').val(),
                        },
                        success: function() { 
                            // close the popup
                            location.reload()
                        }
                    });
                }
            }
        },
        onContentReady: function () {
            // bind to events
            var jc = this;
            this.$content.find('form').on('submit', function (e) {
                // if the user submits the form by pressing enter in the field.
                e.preventDefault();
                jc.$$formSubmit.trigger('click'); // reference the button and click it
            });
        }
    });

    $(this).find('.reject').confirm({
        title: 'Rejet du mail',
        backgroundDismiss: true,
        type: 'red',
        content: '' +
        '<form action="">' +
        '<div class="form-group">' +
        '<label>Motif du rejet</label>' +
        '<textarea style="resize: none;" placeholder="Optionnel" class="explanation form-control"></textarea>' +
        '</div>' +
        '</form>',
        buttons: {
            formSubmit: {
                text: 'Rejeter',
                btnClass: 'btn-red',
                action: function () {
                    $.ajax({
                        url: '/campus/mails/rejeter/' + mailid,
                        type: 'POST',
                        data: {
                            'explanation': this.$content.find('.explanation').val(),
                            'csrfmiddlewaretoken': this.$content.find('input[name="csrfmiddlewaretoken"]').val(),
                        },
                        success: function() { 
                            // close the popup
                            location.reload()
                        }
                    });
                }
            }
        },
        onContentReady: function () {
            // bind to events
            var jc = this;
            this.$content.find('form').on('submit', function (e) {
                // if the user submits the form by pressing enter in the field.
                e.preventDefault();
                jc.$$formSubmit.trigger('click'); // reference the button and click it
            });
        }
    });
});
