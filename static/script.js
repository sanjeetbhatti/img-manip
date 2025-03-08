/**
 * Handle form submission for image upload.
 * Shows loading spinner, uploads file, and displays results or errors.
 * 
 * @param {Event} e - The form submission event
 */
document.getElementById('uploadForm').onsubmit = async (e) => {
    e.preventDefault();
    const spinner = document.getElementById('uploadSpinner');
    spinner.style.display = 'block';
    document.getElementById('result').innerText = '';
    document.getElementById('downloadLinkContainer').style.display = 'none';
    document.getElementById('fileStats').style.display = 'none';
    try {
        const formData = new FormData(e.target);
        const response = await fetch('/upload/', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        
        if (response.ok) {
            // Success case
            document.getElementById('result').innerText = result.message || result.error;
            if (result.url) {
                const downloadLink = document.getElementById('downloadLink');
                downloadLink.href = result.url;
                document.getElementById('downloadLinkContainer').style.display = 'block';
                
                // Display file stats
                if (result.stats) {
                    displayFileStats(result.stats);
                }
                
                setTimeout(getAllPreviousResults, 2000);
            }
        } else {
            // Error case (400, 500, etc.)
            const errorMessage = result.detail || result.error || 'An error occurred during upload.';
            document.getElementById('result').innerText = errorMessage;
        }
    } catch (err) {
        document.getElementById('result').innerText = 'An error occurred during upload.';
    } finally {
        spinner.style.display = 'none';
    }
};

/**
 * Display file statistics in a Bootstrap card.
 * Shows original size, compressed size, compression ratio, quality, and format.
 * 
 * @param {Object} stats - File statistics object
 * @param {number} stats.original_size - Original file size in bytes
 * @param {number} stats.compressed_size - Compressed file size in bytes
 * @param {number} stats.compression_ratio - Compression percentage
 * @param {string} stats.format - File format (JPEG/PNG)
 * @param {number} stats.quality - Quality setting used
 */
function displayFileStats(stats) {
    const statsContainer = document.getElementById('fileStats');
    const originalSizeKB = (stats.original_size / 1024).toFixed(1);
    const compressedSizeKB = (stats.compressed_size / 1024).toFixed(1);
    
    statsContainer.innerHTML = `
        <div class="card mt-3">
            <div class="card-header">
                <h6 class="mb-0">File Statistics</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-6">
                        <small class="text-muted">Original Size</small>
                        <div class="fw-bold">${originalSizeKB} KB</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">Compressed Size</small>
                        <div class="fw-bold">${compressedSizeKB} KB</div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-6">
                        <small class="text-muted">Compression</small>
                        <div class="fw-bold text-success">${stats.compression_ratio}% smaller</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">Quality</small>
                        <div class="fw-bold">${stats.quality}%</div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-12">
                        <small class="text-muted">Format</small>
                        <div class="fw-bold">${stats.format}</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    statsContainer.style.display = 'block';
}

/**
 * Fetch and display all previous image results.
 * Retrieves the last 5 processed images from the server and displays them
 * in the previous results section.
 */
function getAllPreviousResults() {
    fetch('/images')
        .then(response => response.json())
        .then(data => {
            let imagesList = document.getElementById('images-list');
            imagesList.innerHTML = '';

            // Show only last 5 results
            const lastFiveImages = data.images.slice(-5);
            lastFiveImages.forEach(image => {
                let listItem = document.createElement('li');
                let link = document.createElement('a');
                link.href = image[1];
                link.textContent = image[0];
                listItem.appendChild(link);
                imagesList.appendChild(listItem);
            });
            if (lastFiveImages.length > 0) {
                document.getElementById('prev-res').style.display = 'block';
            }
        })
        .catch(error => console.error(error));
}

/**
 * Initialize the application by loading previous results on page load.
 */
window.addEventListener('load', () => {
    getAllPreviousResults();
});
