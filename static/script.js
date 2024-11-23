document.getElementById('uploadForm').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const response = await fetch('/upload/', {
        method: 'POST',
        body: formData
    });
    const result = await response.json();
    document.getElementById('result').innerText = result.message || result.error;
    if (result.url) {
        const downloadLink = document.getElementById('downloadLink');
        downloadLink.href = result.url;
        document.getElementById('downloadLinkContainer').style.display = 'block';
    }
};