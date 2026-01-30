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
function showImagePreview(file) {
    const reader = new FileReader();

    reader.onload = (e) => {
        previewImage = e.target.result;

        // Find preview container
        let previewContainer = document.querySelector('[data-preview-container]') ||
            document.querySelector('.relative.group.w-full.aspect-\\[4\\/3\\]');

        if (previewContainer) {
            // Find image element
            let imgElement = previewContainer.querySelector('img');
            if (imgElement) {
                imgElement.src = previewImage;
                imgElement.alt = file.name;
            }

            // Update filename display
            const filenameEl = previewContainer.querySelector('.text-xs.font-bold.truncate');
            if (filenameEl) {
                filenameEl.textContent = file.name;
            }

            // Update file size display
            const filesizeEl = previewContainer.querySelector('.text-\\[10px\\]');
            if (filesizeEl) {
                const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                filesizeEl.textContent = `${sizeMB} MB`;
            }
        }
    };

    reader.readAsDataURL(file);
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
