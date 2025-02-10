document.getElementById('uploadForm').onsubmit = async (e) => {
    e.preventDefault();
    const spinner = document.getElementById('uploadSpinner');
    spinner.style.display = 'block';
    document.getElementById('result').innerText = '';
    document.getElementById('downloadLinkContainer').style.display = 'none';
    try {
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
            setTimeout(getAllPreviousResults, 2000);
        }
    } catch (err) {
        document.getElementById('result').innerText = 'An error occurred during upload.';
    } finally {
        spinner.style.display = 'none';
    }
};

function getAllPreviousResults() {
    fetch('/images')
        .then(response => response.json())
        .then(data => {
            let imagesList = document.getElementById('images-list');
            imagesList.innerHTML = '';

            // TODO: Iterate over last 5 results only
            data.images.forEach(image => {
                let listItem = document.createElement('li');
                let link = document.createElement('a');
                link.href = image[1];
                link.textContent = image[0];
                listItem.appendChild(link);
                imagesList.appendChild(listItem);
            });
            if (data.images.length > 0) {
                document.getElementById('prev-res').style.display = 'block';
            }
        })
        .catch(error => console.error(error));
}

window.addEventListener('load', () => {
    getAllPreviousResults();
});
