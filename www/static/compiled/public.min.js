
$(document).ready(function () {

    // JavaScript for public facing pages
    
    $('.carousel').carousel({
        interval: 5000
    })

    $('#contact-form button').click(function(event) {
        $('#contact-form').html('<p>Thank You!</p>')
    });

});
