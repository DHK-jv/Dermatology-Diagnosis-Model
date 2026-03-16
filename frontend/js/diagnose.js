/**
 * Logic Trang Chẩn đoán / Tải lên
 * Xử lý tải ảnh, xem trước và gọi phán đoán
 */

let selectedFile = null;
let previewImage = null;

// Khởi tạo trang khi DOM đã tải xong
document.addEventListener('DOMContentLoaded', function () {
    console.log('Diagnosis page initialized');

    setupFileUpload();
    setupCameraCapture();
    setupAnalyzeButton();
});

/**
 * Thiết lập các trình xử lý việc tải ảnh lên
 */
function setupFileUpload() {
    const dropzone = document.querySelector('[data-upload-zone]') ||
        document.querySelector('.group.relative.flex.flex-col.items-center');
    const fileInput = document.getElementById('file-input') || createFileInput();

    if (!dropzone) return;

    // Nhấn chuột để tải file
    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    // Sự kiện khi input chọn file thay đổi
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileSelect(file);
        }
    });

    // Kéo thả (Drag and drop)
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
 * Tạo thẻ input chọn file bị ẩn đi nếu chưa code có sẵn trên diện mạo
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
 * Xử lý sau khi tệp tin đã được chọn thành công
 * @param {File} file - File ảnh
 */
function handleFileSelect(file) {
    console.log('File selected:', file.name);

    // Kiểm tra tính hợp lệ của ảnh
    const validation = validateImage(file);
    if (!validation.valid) {
        showError(validation.error);
        return;
    }

    selectedFile = file;

    // Hiển thị lên màn hình xem trước
    showImagePreview(file);

    showSuccess('Ảnh đã được chọn. Nhấn "Phân tích" để bắt đầu.');
}

/**
 * Hiển thị xem trước hình ảnh và kích hoạt tiền xử lý phân tích
 * @param {File} file - Tệp đồ họa
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

        // Hiện danh sách dạng grid, ẩn nội dung giữ chỗ ban đàu
        const previewGrid = document.getElementById('preview-grid');
        const fileInfoBar = document.getElementById('file-info-bar');

        if (previewGrid) {
            // Gỡ bỏ style='display: none;' nếu đang bị kẹt lại
            previewGrid.removeAttribute('style');
            // Đảm bảo thuộc tính lớp css có chứa flex và thu hồi class hidden
            previewGrid.classList.remove('hidden');
            previewGrid.classList.add('flex');
        } else {
            console.error("Critical: #preview-grid element not found in DOM");
        }

        if (fileInfoBar) {
            fileInfoBar.classList.remove('hidden');
            fileInfoBar.style.display = 'flex';
        }

        // Cập nhật Ảnh Gốc (Original Image)
        const previewContainer = document.querySelector('[data-preview-container]');
        if (previewContainer) {
            const imgElement = previewContainer.querySelector('img');
            if (imgElement) {
                imgElement.src = previewImage;
                imgElement.alt = file.name;
                // Buộc vẽ lại / Cập nhật khung ảnh gốc
                imgElement.style.display = 'block';
                console.log("Image src set. Container found.");
            } else {
                console.error("Critical: img element not found inside [data-preview-container]");
            }
        } else {
            console.error("Critical: [data-preview-container] selector failed");
        }

        // Cập nhật Thông Tin Của Tệp (File Info)
        const filenameEl = document.getElementById('filename-display');
        const filesizeEl = document.getElementById('filesize-display');

        if (filenameEl) filenameEl.textContent = file.name;
        if (filesizeEl) {
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            filesizeEl.textContent = `${sizeMB} MB`;
        }

        // Kích hoạt chức năng Tạm Lướt Tiền xử lý (Preprocessing Preview)
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
 * Làm mới (Reset) lại trạng thái cửa sổ tải lên
 */
window.resetUpload = function () {
    selectedFile = null;
    previewImage = null;

    // Ẩn bảng hiển thị xem trước
    const previewGrid = document.getElementById('preview-grid');
    const fileInfoBar = document.getElementById('file-info-bar');
    if (previewGrid) previewGrid.style.display = 'none';
    if (fileInfoBar) fileInfoBar.classList.add('hidden');

    // Format lại trạng thái (Reset file input)
    const fileInput = document.getElementById('file-input');
    if (fileInput) fileInput.value = '';

    console.log('Upload reset');
}

async function fetchPreprocessingPreview(file) {
    const loadingEl = document.getElementById('processed-loading');

    // Trạng thái Giao diện Bắt đầu
    if (loadingEl) loadingEl.classList.remove('hidden');

    try {
        // Tạo bộ dữ liệu Form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('return_steps', 'true');

        console.log("DEBUG: API_CONFIG before fetch:", API_CONFIG);

        const data = await apiCall(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PREVIEW}`, {
            method: 'POST',
            body: formData
        });

        // Hiện Hoạt Ảnh đồ họa (Animation) phân tích tiền xử lý
        if (data.steps) {
            await runPreprocessingAnimation(data.steps);
        }

    } catch (error) {
        const baseUrl = (typeof API_CONFIG !== 'undefined' && API_CONFIG.BASE_URL) ? API_CONFIG.BASE_URL : 'unknown';
        console.error('Preview error:', error, 'Base URL:', baseUrl);

        // Hiển thị trạng thái phát sinh hiện tượng Lỗi
        const statusEl = document.getElementById('step-status');
        const statusLabel = document.getElementById('step-label');
        if (statusEl && statusLabel) {
            statusEl.classList.remove('hidden');
            statusEl.classList.replace('bg-black/70', 'bg-red-500/90');
            statusEl.querySelector('span').classList.remove('bg-green-500', 'animate-pulse');
            statusEl.querySelector('span').classList.add('bg-white');
            statusLabel.textContent = "Preview Error";
        }
        if (typeof showError === 'function') {
            showError(error?.message || 'Preview Error');
        }
    } finally {
        if (loadingEl) loadingEl.classList.add('hidden');
    }
}

/**
 * Chạy hiệu ứng xem trước ảnh đã được xử lý
 * @param {Object} steps - Dictionary của bộ mã định dạng base64 chứa hình xử lý {step_name: base64_string}
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

    // Đặt lại các tín hiệu trạng thái UI
    statusEl.classList.remove('hidden');
    statusEl.classList.replace('bg-red-500/90', 'bg-black/70');
    statusEl.querySelector('span').classList.remove('bg-white');
    statusEl.querySelector('span').classList.add('bg-green-500', 'animate-pulse');

    // Thiết lập trật tự biến đổi phân đoạn hình ảnh
    const sequence = [
        { key: 'original', label: 'Original Image', delay: 1000 },
        { key: 'cropped', label: '1. Segmentation (Cropping)', delay: 1000 },
        { key: 'resized', label: '2. Resize (380x380)', delay: 1000 },
        { key: 'hair_removed', label: '3. Hair Removal', delay: 1200 },
        { key: 'normalized', label: '4. Normalization (Final)', delay: 0 }
    ];

    // Quét bao gồm qua ảnh 'original' (nếu chưa có trong object payload API)

    // Lặp theo từng chuỗi phân tích
    for (const step of sequence) {
        if (step.key === 'original') {
            // Chỉ có thể thay đổi trên trạng thái mô tả Text (ảnh original đã cố định từ lúc người dùng upload ảnh rồi)
            statusLabel.textContent = step.label;
        } else if (steps[step.key]) {
            // Cập nhật nhãn và thay hình ảnh
            statusLabel.textContent = step.label;

            // Chỉnh mờ hình ảnh từ từ
            imgElement.style.opacity = '0.8';

            await new Promise(r => setTimeout(r, 100));

            imgElement.src = steps[step.key];
            imgElement.style.opacity = '1';
        } else {
            continue; // Bỏ qua nếu các bước tiến quá nhanh mà API chưa kịp gửi response
        }

        if (step.delay > 0) {
            await new Promise(r => setTimeout(r, step.delay));
        }
    }

    // Chuỗi xử lý đồ họa Animation đã hoàn tất
    statusEl.classList.replace('bg-black/70', 'bg-primary/90');
    statusLabel.textContent = "Ready for Analysis";
    statusEl.querySelector('span').classList.remove('animate-pulse');
}

/**
 * Thiết lập nhấn mở nút Cụm tùy chọn chụp Máy Ảnh (Camera)
 */
function setupCameraCapture() {
    const cameraBtn = document.querySelector('[data-camera-btn]') ||
        Array.from(document.querySelectorAll('button')).find(btn =>
            btn.textContent.includes('Camera') || btn.textContent.includes('Sử Dụng Camera')
        );

    if (!cameraBtn) return;

    cameraBtn.addEventListener('click', async () => {
        try {
            // Yêu cầu quyền truy cập Camera từ Browser
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' } // Ưu tiên chọn cụm camera mặt sau của Di động (back camera)
            });

            // Tạo phần tử thẻ DOM video phát trực tiếp luồng camera
            const video = document.createElement('video');
            video.srcObject = stream;
            video.autoplay = true;

            // Hiển thị khung video xem trước camera (hiện tại tính năng thu hình chưa có nên sẽ bắt Lỗi thông báo tới người dùng)
            showError('Chức năng camera đang được phát triển. Vui lòng upload ảnh từ thư viện.');

            // Hủy/Stop quá trình ghi hình ảnh
            stream.getTracks().forEach(track => track.stop());

        } catch (error) {
            console.error('Camera error:', error);
            showError('Không thể truy cập camera. Vui lòng upload ảnh từ thư viện.');
        }
    });
}

/**
 * Thiết lập lắng nghe sự kiện nút Bắt đầu Phân tích (Analyze)
 */
function setupAnalyzeButton() {
    // Nhắm mục tiêu dùng html attribute chứa selector (thuộc tính data) trước, sau đó tra text dự phòng
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
 * Khởi chạy chu trình chẩn đoán (Diagnostic API execution)
 */
async function runDiagnosis() {
    if (!selectedFile) {
        showError('Vui lòng chọn ảnh');
        return;
    }

    try {
        showLoader('Đang tải ảnh lên server...');

        // Khởi tạo Form chứa tệp tin ảnh gửi đi
        const formData = new FormData();
        formData.append('file', selectedFile);

        // Cập nhật chuỗi thông điệp tiến độ trên form Loader
        setTimeout(() => {
            const loaderMsg = document.getElementById('loader-message');
            if (loaderMsg) loaderMsg.textContent = 'AI đang phân tích ảnh...';
        }, 1000);

        // Gửi hàm xử lý qua apiCall thay vì fetch để đính kèm Token đăng nhập
        const result = await apiCall(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PREDICT}`, {
            method: 'POST',
            body: formData
        });

        console.log('Diagnosis result:', result);

        hideLoader();

        // Lưu trữ object response (đáp ứng) để phục vụ qua trang kết quả (result page) hiển thị
        store('latestDiagnosis', result);

        // Lưu lại hình khối base64 của bức hình Gốc (phục hồi cho vẽ Overlay xử lý GradCAM ở trang result)
        if (previewImage) {
            try {
                sessionStorage.setItem(`recentImage_${result.diagnosis_id}`, previewImage);
            } catch (e) {
                console.warn('Could not save image to sessionStorage (too large?):', e);
            }
        }

        // Điều hướng chuyến tiếp giao diện người dùng tới trang result HTML
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
