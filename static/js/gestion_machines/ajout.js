jQuery(document).ready(function ($) {
    // Créer fonction qui disable le bouton si l'alias choisi n'est pas dispo
    $('#id_alias').keyup(function () {
        var length = $('#id_alias').val().length;

        if (length > 0) {
            $('#bouton').prop('disabled', true);
        } else {
            $('#bouton').prop('disabled', false);
        }
    });
});