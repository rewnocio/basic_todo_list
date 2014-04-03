$.fn.serializeObject = () ->
    values = this.serializeArray();
    return _.chain(values)
            .map( (el) -> [el.name, el.value] )
            .object()
            .value()

Datafly.alert = (el) ->
    $('#alert' + el)
        .removeClass('hidden')
        .slideDown('slow')
        .delay(6000).slideUp('slow')

Datafly.notify = (msg) ->
    $('.center').notify(
        message: 
            text: msg
    ).show()

Datafly.error = (msg) ->
    $('.center').notify(
        type: 'danger',
        message: 
            text: msg
    ).show()

Datafly.submit = (event) ->
    event.preventDefault();
    $form = $(this).parents('form')
    reload = $(this).data('reload')
    redirect = $(this).data('redirect')
    success = $(this).data('success')
    $.ajax(
        url: $form.attr('action'),
        type: 'POST'
        data: $form.serialize()
    ).done (data) ->         
        success = success or data.success
        if reload
            window.location.reload()
        else if success
            Datafly.alert(success)
        else if data.error is false
            location.href = redirect or data.redirect
        else
            Datafly.alert(data.error)

$ () ->

    $('#login .btn').click(Datafly.submit)

    $('#post-logout').click (event) ->
        $(this).next('form').submit()