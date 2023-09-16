$(document).ready(function () {
    // Handle paste submissions
    $('#sendPaste').submit(function (event) {
        event.preventDefault()
        const formData = new FormData(this)
        formData.set('method', 'paste-text')
        const data = Object.fromEntries(formData.entries())
        const jsonData = JSON.stringify(data)
        console.log(`data: ${jsonData}`)
        socket.send(jsonData)
    })
})
