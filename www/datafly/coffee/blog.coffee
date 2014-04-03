$(document).ready ->     

    $('table.blog .del, table.blog .undel').click (event) ->
        event.preventDefault();
        data = 
            'meta.hide': $(this).hasClass('del')        
        # send { 'hide': true/false } to API
        $.ajax(
            url: '/admin/api/pages/' + $(this).data('id'),
            type: 'POST',
            data: data
        );        
        # swap control links and style
        $post = $(this).parents('tr');
        $post.find('.del, .undel').toggleClass('hide')
        $post.toggleClass('disabled');
