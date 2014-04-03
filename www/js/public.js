
$(document).ready(function () {

    // JavaScript for public facing pages
    
    $('.carousel').carousel({
        interval: 5000
    })

    $('#contact-form button').click(function(event) {
        $('#contact-form').html('<p>Thank You!</p>')
    });

    // handling task changing
    $('td').dblclick(function(event) {
        // getting hidden input
        var $child = $(this).children('input');
		
	// changing content
	$(this).html($child);
	$(this).children('input').attr("type", "text").prop("disabled", false);
		
	return false;
    });

});
