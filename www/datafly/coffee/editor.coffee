Datafly.redactor_buttons = [
    'formatting', '|',
    'bold', 'italic', 'link', '|',
    'unorderedlist', 'orderedlist', '|',
    'alignment', '|',
    'indent', 'outdent', 'table', '|',
    'image', 'file', 'video',
    'html'
]

$ () ->

    $('.dropdown-toggle').dropdown()

    $('#versions a').click ->
        $('#versions li').removeClass('active');
        $(this).parent('li').addClass('active');
        v = $(this).text()
        id = $(this).data('id')
        $.ajax(
            url: """/admin/api/pages/#{id}/version"""
            type: 'GET'
        ).done((data) ->
            $('[data-clip]').each ->    
                clip = $(this).attr('data-clip')           
                if $(this).is 'img'
                    src = data.img[clip]
                    $(this).attr('src', src)
                else
                    html = data[clip]
                    $(this).redactor('set', html)
        )        
        Datafly.notify """Loaded from #{v}"""

    $('div[data-clip]').each ->
        clip = $(this).data('clip')
        $('.toolbar-redactor').append(
            """<div id="toolbar-#{clip}"></div>"""
        )
        $(this).redactor(
            buttons: Datafly.redactor_buttons
            imageUpload: '/admin/upload/img'
            fileUpload: '/admin/upload/file'
            toolbarExternal: "#toolbar-#{clip}"
            plugins: ['externalswitcher']
        )

    # focus top redactor
    $('div[data-clip]').first().redactor 'focus'

    $('#save').click ->
        # check required fields
        valid = true
        $('form#meta [data-required]').each ->
            label = $(this).prev('label')
            if $(this).val() is ''
                label.css('color', 'red')
                valid = false
            else
                label.css('color', '#aaa')            
        return Datafly.error 'Please fill all required fields.' if !valid
        # save
        page =
            img: {}
            meta: $('form#meta').serializeObject()                
        $('[data-clip]').each ->            
            clip = $(this).data('clip')
            if $(this).is 'img'
                src = $(this).attr('src')
                page.img[clip] = src
            else
                html = $(this).redactor('get')
                page[clip] = html
        page['id'] = id = $(this).data('page-id')
        $.ajax(
            url: "/admin/api/pages/id/#{ id }"
            type: 'POST'
            data: JSON.stringify(
                page: page
            ),
            dataType: 'json',
            contentType: 'application/json'
            success: (res) -> $('#save').data('page-id', res.id)
        )
        Datafly.notify 'New version published!'

    $('#hidden-upload-redactor').redactor(
        buttons: Datafly.redactor_buttons
        imageUpload: '/admin/upload/img'
        fileUpload: '/admin/upload/file'
        imageUploadCallback: (image, json) ->
            replaceImage = $("[data-clip=#{ Datafly.replaceImage }]")                        
            replaceImage.attr('src', json.filelink)
    )

    $('.content').on 'click', 'img[data-clip]', (event) ->
        img = $(event.currentTarget)
        Datafly.replaceImage = img.attr('data-clip')
        options = $('#hidden-upload-redactor').redactor('getObject').opts
        options.imageUpload = "/admin/upload/img"
        fitWidth = img.data('fit-width')
        fitHeight = img.data('fit-height')        
        crop = img.data('crop') || 'yes';        
        if fitWidth and fitHeight
            options.imageUpload = (options.imageUpload +
                "?width=#{ fitWidth }&height=#{ fitHeight }&crop=#{ crop }")
        $('#hidden-upload .redactor_btn_image').click()