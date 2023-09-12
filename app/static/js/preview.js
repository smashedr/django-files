$(document).ready(function () {
    // Get and set the csrf_token
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value

    // Define Hook Modal and Delete handlers
    const deleteHookModal = new bootstrap.Modal('#deleteFileModal', {})
    let hookID
    $('.delete-file-btn').click(function () {
        hookID = $(this).data('hook-id')
        console.log(hookID)
        deleteHookModal.show()
    })

    // Handle delete click confirmations
    $('#confirmDeleteFileBtn').click(function () {
        console.log(hookID)
        $.ajax({
            type: 'POST',
            url: `/ajax/delete/file/${hookID}/`,
            headers: { 'X-CSRFToken': csrftoken },
            beforeSend: function () {
                console.log('beforeSend')
            },
            success: function (response) {
                console.log('response: ' + response)
                deleteHookModal.hide()
                console.log('removing #file-' + hookID)
                let count = $('#files-table tr').length
                $('#file-' + hookID).remove()
                if (count <= 2) {
                    console.log('removing #files-table@ #files-table')
                    $('#files-table').remove()
                }
                let message = 'File ' + hookID + ' Successfully Removed.'
                show_toast(message, 'success')
            },
            error: function (xhr, status, error) {
                console.log('xhr status: ' + xhr.status)
                console.log('status: ' + status)
                console.log('error: ' + error)
                deleteHookModal.hide()
                let message = xhr.status + ': ' + error
                show_toast(message, 'danger', '15000')
            },
            complete: function () {
                console.log('complete')
                window.location.replace('/files/')
            },
        })
    })

    // Set Password Hook Modal and Set Password handlers
    const setPasswordHookModal = new bootstrap.Modal(
        '#setFilePasswordModal',
        {}
    )
    let pwhookID
    $('.set-password-file-btn').click(function () {
        pwhookID = $(this).data('hook-id')
        console.log(pwhookID)
        setPasswordHookModal.show()
    })

    // Handle set password click confirmations
    $('#confirm-set-password-hook-btn').click(function (event) {
        event.preventDefault()
        if ($('#confirm-set-password-hook-btn').hasClass('disabled')) {
            return
        }
        let formData = new $('#set-password-form').serialize()
        console.log(formData)
        console.log(pwhookID)
        $.ajax({
            type: 'POST',
            url: `/ajax/set_password/file/${pwhookID}/`,
            headers: { 'X-CSRFToken': csrftoken },
            data: formData,
            beforeSend: function () {
                console.log('beforeSend')
                $('#confirm-set-password-hook-btn').addClass('disabled')
            },
            success: function (response) {
                console.log('response: ' + response)
                setPasswordHookModal.hide()
                let message = 'Password set!'
                show_toast(message, 'success')
            },
            error: function (xhr, status, error) {
                console.log('xhr status: ' + xhr.status)
                console.log('status: ' + status)
                console.log('error: ' + error)
                setPasswordHookModal.hide()
                let message = xhr.status + ': ' + error
                show_toast(message, 'danger', '15000')
            },
            complete: function () {
                console.log('complete')
                $('#confirm-set-password-hook-btn').removeClass('disabled')
            },
        })
    })

    // Handle toggling file private status
    $('#toggle-private-btn').click(function (event) {
        event.preventDefault()
        let pvhookID = $(this).data('hook-id')
        if ($('#toggle-private-btn').hasClass('disabled')) {
            return
        }
        console.log(pvhookID)
        let private_status = $('#privateStatus')
        let toggle_status = $('#toggleStatus')
        let toggle_text = $('#toggleText')
        $.ajax({
            type: 'POST',
            url: `/ajax/toggle_private/file/${pvhookID}/`,
            headers: { 'X-CSRFToken': csrftoken },
            success: function (response) {
                console.log('response: ' + response)
                let isTrueSet = response === 'True'
                let message
                if (isTrueSet) {
                    message = 'File made private!'
                    private_status.title = 'Private File'
                    private_status
                        .removeClass('fa-lock-open')
                        .addClass('fa-lock')
                    toggle_status
                        .removeClass('fa-lock')
                        .addClass('fa-lock-open')
                    toggle_text.text(
                        toggle_text.text().replace('Private', 'Public')
                    )
                } else {
                    message = 'File made public!'
                    private_status.title = 'Public File'
                    private_status
                        .removeClass('fa-lock')
                        .addClass('fa-lock-open')
                    toggle_status
                        .removeClass('fa-lock-open')
                        .addClass('fa-lock')
                    toggle_text.text(
                        toggle_text.text().replace('Public', 'Private')
                    )
                }
                show_toast(message, 'success')
            },
            error: function (xhr, status, error) {
                console.log('xhr status: ' + xhr.status)
                console.log('status: ' + status)
                console.log('error: ' + error)
                let message = xhr.status + ': ' + error
                show_toast(message, 'danger', '15000')
            },
        })
    })

    $('#unMaskPassword').click(function () {
        let password_field = $('#password').get(0)
        if (password_field.type === 'password') {
            password_field.type = 'text'
        } else {
            password_field.type = 'password'
        }
    })

    $('#copyPassword').click(function () {
        let password_field = $('#password').get(0)
        navigator.clipboard.writeText(password_field.value)
        show_toast('Password copied!', 'info', '15000')
    })

    $('#generatePassword').click(function () {
        // TODO: Cleanup this Listener
        let chars =
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        let passwordLength = 12
        let password = ''
        for (var i = 0; i <= passwordLength; i++) {
            var randomNumber = Math.floor(Math.random() * chars.length)
            password += chars.substring(randomNumber, randomNumber + 1)
        }
        $('#password').get(0).value = password
        navigator.clipboard.writeText(password)
        show_toast('Password generated and copied!', 'info', '15000')
    })

    $('#setFilePasswordModal').on('shown.bs.modal', function () {
        $('#password').focus()
    })
})
