/**
 * Diagnosis / Upload Page Logic
 * Handle image upload, preview, and prediction
 */

let selectedFile = null;
let previewImage = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    console.log('Diagnosis page initialized');

    setupFileUpload();
    setupCameraCapture();
    setupAnalyzeButton();
});

/**
 * Setup file upload handlers
 */
function setupFileUpload() {
    const dropzone = document.querySelector('[data-upload-zone]') ||
        document.querySelector('.group.relative.flex.flex-col.items-center');
    const fileInput = document.getElementById('file-input') || createFileInput();

    if (!dropzone) return;

    // Click to upload
    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileSelect(file);
        }
    });

    // Drag and drop
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('border-primary', 'bg-primary/10');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('border-primary', 'bg-primary/10');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-primary', 'bg-primary/10');

        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileSelect(file);
        }
    });
}

/**
 * Create hidden file input if doesn't exist
 */
function createFileInput() {
    let input = document.getElementById('file-input');
    if (!input) {
        input = document.createElement('input');
        input.type = 'file';
        input.id = 'file-input';
        input.accept = 'image/*';
        input.style.display = 'none';
        document.body.appendChild(input);
    }
    return input;
}

/**
 * Handle file selection
 * @param {File} file - Selected file
 */
function handleFileSelect(file) {
    console.log('File selected:', file.name);

    // Validate image
    const validation = validateImage(file);
    if (!validation.valid) {
        showError(validation.error);
        return;
    }

    selectedFile = file;

    // Show preview
    showImagePreview(file);

    showSuccess('Ảnh đã được chọn. Nhấn "Phân tích" để bắt đầu.');
}

/**
 * Show image preview
 * @param {File} file - Image file
 */
/**
 * Show image preview and trigger preprocessing
 * @param {File} file - Image file
 */
function showImagePreview(file) {
    if (typeof FileReader === "undefined") {
        showError("Trình duyệt của bạn không hỗ trợ FileReader.");
        return;
    }

    const reader = new FileReader();

    reader.onload = (e) => {
        console.log("FileReader loaded image successfully");
        previewImage = e.target.result;

        // Show grid, hide placeholder prompt
        const previewGrid = document.getElementById('preview-grid');
        const fileInfoBar = document.getElementById('file-info-bar');

        if (previewGrid) {
            // Remove inline style="display: none;" that might be stuck
            previewGrid.removeAttribute('style');
            // Ensure flex class is active and hidden is removed
            previewGrid.classList.remove('hidden');
            previewGrid.classList.add('flex');
        } else {
            console.error("Critical: #preview-grid element not found in DOM");
        }

        if (fileInfoBar) {
            fileInfoBar.classList.remove('hidden');
            fileInfoBar.style.display = 'flex';
        }

        // Update Original Image
        const previewContainer = document.querySelector('[data-preview-container]');
        if (previewContainer) {
            const imgElement = previewContainer.querySelector('img');
            if (imgElement) {
                imgElement.src = previewImage;
                imgElement.alt = file.name;
                // Force a redraw/check
                imgElement.style.display = 'block';
                console.log("Image src set. Container found.");
            } else {
                console.error("Critical: img element not found inside [data-preview-container]");
            }
        } else {
            console.error("Critical: [data-preview-container] selector failed");
        }

        // Update File Info
        const filenameEl = document.getElementById('filename-display');
        const filesizeEl = document.getElementById('filesize-display');

        if (filenameEl) filenameEl.textContent = file.name;
        if (filesizeEl) {
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            filesizeEl.textContent = `${sizeMB} MB`;
        }

        // Trigger Preprocessing Preview
        if (typeof API_CONFIG !== 'undefined') {
            fetchPreprocessingPreview(file);
        } else {
            console.error("API_CONFIG is not defined, cannot fetch preview");
        }
    };

    reader.onerror = (e) => {
        console.error("FileReader error:", e);
        showError("Lỗi khi đọc file ảnh.");
    };

    reader.readAsDataURL(file);
}


/**
 * Reset upload state
 */
window.resetUpload = function () {
    selectedFile = null;
    previewImage = null;

    // Hide preview
    const previewGrid = document.getElementById('preview-grid');
    const fileInfoBar = document.getElementById('file-info-bar');
    if (previewGrid) previewGrid.style.display = 'none';
    if (fileInfoBar) fileInfoBar.classList.add('hidden');

    // Reset file input
    const fileInput = document.getElementById('file-input');
    if (fileInput) fileInput.value = '';

    console.log('Upload reset');
}

async function fetchPreprocessingPreview(file) {
    const loadingEl = document.getElementById('processed-loading');

    // UI Start State
    if (loadingEl) loadingEl.classList.remove('hidden');

    try {
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('return_steps', 'true');

        console.log("DEBUG: API_CONFIG before fetch:", API_CONFIG);

        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PREVIEW}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Preview failed');
        }

        const data = await response.json();

        // Run Animation
        if (data.steps) {
            await runPreprocessingAnimation(data.steps);
        }

    } catch (error) {
        console.error('Preview error:', error);

        // Show status error
        const statusEl = document.getElementById('step-status');
        const statusLabel = document.getElementById('step-label');
        if (statusEl && statusLabel) {
            statusEl.classList.remove('hidden');
            statusEl.classList.replace('bg-black/70', 'bg-red-500/90');
            statusEl.querySelector('span').classList.remove('bg-green-500', 'animate-pulse');
            statusEl.querySelector('span').classList.add('bg-white');
            statusLabel.textContent = "Preview Error";
        }
    } finally {
        if (loadingEl) loadingEl.classList.add('hidden');
    }
}

/**
 * Run the preprocessing animation
 * @param {Object} steps - Dictionary of base64 images {step_name: base64_string}
 */
async function runPreprocessingAnimation(steps) {
    const previewContainer = document.querySelector('[data-preview-container]');
    const imgElement = previewContainer ? previewContainer.querySelector('img') : null;
    const statusEl = document.getElementById('step-status');
    const statusLabel = document.getElementById('step-label');

    if (!imgElement || !statusEl || !statusLabel) {
        console.error("Animation elements not found");
        return;
    }

    // Reset status UI
    statusEl.classList.remove('hidden');
    statusEl.classList.replace('bg-red-500/90', 'bg-black/70');
    statusEl.querySelector('span').classList.remove('bg-white');
    statusEl.querySelector('span').classList.add('bg-green-500', 'animate-pulse');

    // Define sequence
    const sequence = [
        { key: 'original', label: 'Original Image', delay: 1000 },
        { key: 'cropped', label: '1. Segmentation (Cropping)', delay: 1000 },
        { key: 'resized', label: '2. Resize (300x300)', delay: 1000 },
        { key: 'hair_removed', label: '3. Hair Removal', delay: 1200 },
        { key: 'normalized', label: '4. Normalization (Final)', delay: 0 }
    ];

    // Prepare steps including original if available (it might not be in 'steps' object from backend if only processed steps returned)
    // Actually backend returns 'original' in steps? Let's check. 
    // If not, we rely on what's already there (original).

    // Iterate through sequence
    for (const step of sequence) {
        if (step.key === 'original') {
            // Just show status, image is already there or we don't have it in steps payload usually
            statusLabel.textContent = step.label;
        } else if (steps[step.key]) {
            // Update image and label
            statusLabel.textContent = step.label;

            // Fade out slightly
            imgElement.style.opacity = '0.8';

            await new Promise(r => setTimeout(r, 100));

            imgElement.src = steps[step.key];
            imgElement.style.opacity = '1';
        } else {
            continue; // Skip missing steps
        }

        if (step.delay > 0) {
            await new Promise(r => setTimeout(r, step.delay));
        }
    }

    // Animation complete
    statusEl.classList.replace('bg-black/70', 'bg-primary/90');
    statusLabel.textContent = "Ready for Analysis";
    statusEl.querySelector('span').classList.remove('animate-pulse');
}

/**
 * Setup camera capture button
 */
function setupCameraCapture() {
    const cameraBtn = document.querySelector('[data-camera-btn]') ||
        Array.from(document.querySelectorAll('button')).find(btn =>
            btn.textContent.includes('Camera') || btn.textContent.includes('Sử Dụng Camera')
        );

    if (!cameraBtn) return;

    cameraBtn.addEventListener('click', async () => {
        try {
            // Request camera access
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' } // Prefer back camera on mobile
            });

            // Create video element for camera preview
            const video = document.createElement('video');
            video.srcObject = stream;
            video.autoplay = true;

            // Show camera modal (simplified - you can enhance this)
            showError('Chức năng camera đang được phát triển. Vui lòng upload ảnh từ thư viện.');

            // Stop camera
            stream.getTracks().forEach(track => track.stop());

        } catch (error) {
            console.error('Camera error:', error);
            showError('Không thể truy cập camera. Vui lòng upload ảnh từ thư viện.');
        }
    });
}

/**
 * Setup analyze button
 */
function setupAnalyzeButton() {
    // Use data attribute first, then fallback to text search
    const analyzeBtn = document.querySelector('[data-analyze-btn]') ||
        Array.from(document.querySelectorAll('button')).find(btn =>
            btn.textContent.includes('Phân Tích') || btn.textContent.includes('Analyze')
        );

    if (!analyzeBtn) {
        console.warn('Analyze button not found');
        return;
    }

    console.log('✓ Analyze button found:', analyzeBtn);

    analyzeBtn.addEventListener('click', async () => {
        console.log('Analyze button clicked, selectedFile:', selectedFile);

        if (!selectedFile) {
            showError('Vui lòng chọn ảnh trước khi phân tích');
            return;
        }

        await runDiagnosis();
    });
}

/**
 * Run AI diagnosis
 */
async function runDiagnosis() {
    if (!selectedFile) {
        showError('Vui lòng chọn ảnh');
        return;
    }

    try {
        showLoader('Đang tải ảnh lên server...');

        // Create form data
        const formData = new FormData();
        formData.append('file', selectedFile);

        // Update loader message
        setTimeout(() => {
            const loaderMsg = document.getElementById('loader-message');
            if (loaderMsg) loaderMsg.textContent = 'AI đang phân tích ảnh...';
        }, 1000);

        // Call predict API
        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PREDICT}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Lỗi khi gọi API');
        }

        const result = await response.json();
        console.log('Diagnosis result:', result);

        hideLoader();

        // Store result for result page
        store('latestDiagnosis', result);

        // Navigate to result page
        showSuccess('Phân tích hoàn tất!');
        setTimeout(() => {
            navigateTo('result.html', { diagnosisId: result.diagnosis_id });
        }, 500);

    } catch (error) {
        hideLoader();
        console.error('Diagnosis error:', error);
        showError(`Lỗi: ${error.message}`);
    }
}
