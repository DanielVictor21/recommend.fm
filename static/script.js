document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed');
    let postRequestSent = localStorage.getItem('postRequestSent');
    console.log('postRequestSent:', postRequestSent);

    if (!postRequestSent) {
        console.log('Sending POST request...');
        sendPostRequest();
        localStorage.setItem('postRequestSent', 'true');
        console.log('Flag set in localStorage');
    }
});

function sendPostRequest() {
    fetch('/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ data: 'your-data' })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function resetPostFlag() {
    localStorage.removeItem('postRequestSent');
    console.log('Flag reset in localStorage');
}
