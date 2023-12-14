// JS for shorts

const deleteShortModal = $('#delete-short-modal')

// Handle Shorts FORM Submit
$('#shortsForm').on('submit', function (event) {
    console.log('#shortsForm submit', event)
    event.preventDefault()
    let data = new FormData(this)
    data.forEach((value, key) => (data[key] = value))
    $.ajax({
        type: $(this).attr('method'),
        url: $(this).attr('action'),
        data: JSON.stringify(data),
        headers: { 'X-CSRFToken': csrftoken },
        success: function (data) {
            console.log('data:', data)
            alert(`Short Created: ${data.url}`)
            location.reload()
        },
        error: function (jqXHR) {
            if (jqXHR.status === 400) {
                const message = `${jqXHR.status}: ${jqXHR.responseJSON.error}`
                show_toast(message, 'danger', '6000')
            } else {
                const message = `${jqXHR.status}: ${jqXHR.statusText}`
                show_toast(message, 'danger', '6000')
            }
        },
        cache: false,
        contentType: false,
        processData: false,
    })
})

// Define Hook Modal and Delete handlers
// TODO: Use a proper selector
let hookID
$('.delete-short-btn').on('click', function () {
    hookID = $(this).data('hook-id')
    console.log(hookID)
    deleteShortModal.modal('show')
})

// Handle delete click confirmations
$('#short-delete-confirm').on('click', function () {
    console.log(`#short-delete-confirm click hookID: ${hookID}`)
    $.ajax({
        type: 'POST',
        url: `/ajax/delete/short/${hookID}/`,
        headers: { 'X-CSRFToken': csrftoken },
        success: function (data) {
            console.log('data:', data)
            deleteShortModal.modal('hide')
            console.log(`removing #short-${hookID}`)
            $(`#short-${hookID}`).remove()
            const count = $('#shorts-table tr').length
            if (count <= 1) {
                console.log('removing #shorts-table@ #shorts-table')
                $('#shorts-table').remove()
            }
            const message = `Short URL ${hookID} Successfully Removed.`
            show_toast(message, 'success')
        },
        error: function (jqXHR) {
            deleteShortModal.modal('hide')
            const message = `${jqXHR.status}: ${jqXHR.statusText}`
            show_toast(message, 'danger', '6000')
        },
        cache: false,
        contentType: false,
        processData: false,
    })
})
