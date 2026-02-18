/**
 * Result Page Logic
 * Display diagnosis results with details
 */

// Import from medical-terms.js for centralized disease name translations
import { DISEASE_NAMES, RISK_LEVELS, MEDICAL_LOGO } from '../js/medical-terms.js';

/**
 * Translate disease name from English to Vietnamese
 * @param {string} englishName - English disease name
 * @returns {string} Vietnamese disease name with English in parentheses
 */
function translateDiseaseName(englishName) {
    if (!englishName) return '';

    const normalized = englishName.toLowerCase().trim().replace(/\s+/g, '_');
    return DISEASE_NAMES[normalized] || englishName;
}

/**
 * Translate risk level from English to Vietnamese
 * @param {string} riskLevel - English risk level
 * @returns {string} Vietnamese risk level
 */
function translateRiskLevel(riskLevel) {
    if (!riskLevel) return '';

    const normalized = riskLevel.toLowerCase().trim();
    return RISK_LEVELS[normalized] || riskLevel;
}

let currentDiagnosis = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async function () {
    console.log('Result page initialized');

    await loadDiagnosisResult();
    setupResultActions();
});

/**
 * Load and display diagnosis result
 */
async function loadDiagnosisResult() {
    try {
        // Try to get from navigation state first
        const navState = getNavigationState();
        const diagnosisId = navState?.diagnosisId || new URLSearchParams(window.location.search).get('id');

        // Try localStorage (latest diagnosis)
        let diagnosis = retrieve('latestDiagnosis');

        // If we have a specific ID, fetch from API
        if (diagnosisId && (!diagnosis || diagnosis.diagnosis_id !== diagnosisId)) {
            showLoader('Đang tải kết quả...');

            try {
                diagnosis = await apiCall(
                    API_CONFIG.BASE_URL + API_CONFIG.ENDPOINTS.DIAGNOSIS(diagnosisId)
                );
            } catch (error) {
                hideLoader();
                showError('Không tìm thấy kết quả chẩn đoán');
                return;
            }

            hideLoader();
        }

        if (!diagnosis) {
            showError('Không tìm thấy kết quả chẩn đoán');
            setTimeout(() => {
                window.location.href = 'intro.html';
            }, 2000);
            return;
        }

        currentDiagnosis = diagnosis;
        displayDiagnosisResult(diagnosis);

    } catch (error) {
        console.error('Error loading diagnosis:', error);
        showError('Lỗi khi tải kết quả');
    }
}

/**
 * Display diagnosis result on page
 * @param {object} diagnosis - Diagnosis data
 */
function displayDiagnosisResult(diagnosis) {
    console.log('Displaying diagnosis:', diagnosis);

    // Update diagnosis ID
    updateElement('[data-diagnosis-id]', diagnosis.diagnosis_id);

    // Translate and update disease name
    const diseaseNameVi = diagnosis.disease_name_vi || translateDiseaseName(diagnosis.disease_name || diagnosis.disease_name_en);
    const diseaseNameEn = diagnosis.disease_name_en || diagnosis.disease_name || '';

    updateElement('[data-disease-name]', diseaseNameVi);
    updateElement('[data-disease-name-en]', diseaseNameEn);

    // Update confidence
    updateElement('[data-confidence]', diagnosis.confidence_percent);
    updateElement('[data-confidence-value]', `${(diagnosis.confidence * 100).toFixed(1)}%`);

    // Update confidence circle/progress
    updateConfidenceProgress(diagnosis.confidence);

    // Translate and update risk level
    const riskLevelVi = diagnosis.risk_level_vi || translateRiskLevel(diagnosis.risk_level);
    updateRiskLevel(diagnosis.risk_level, riskLevelVi);

    // Update recommendations
    updateRecommendations(diagnosis.recommendations);

    // Update timestamp
    updateElement('[data-timestamp]', formatDate(diagnosis.timestamp));

    // Update all predictions
    updateAllPredictions(diagnosis.all_predictions);
}

/**
 * Update element content by selector
 * @param {string} selector - CSS selector
 * @param {string} content - New content
 */
function updateElement(selector, content) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
        if (el) el.textContent = content;
    });
}

/**
 * Update confidence progress circle
 * @param {number} confidence - Confidence value (0-1)
 */
function updateConfidenceProgress(confidence) {
    const percent = confidence * 100;

    // Find SVG circle
    const circles = document.querySelectorAll('circle[stroke-dasharray]');
    circles.forEach(circle => {
        // Calculate stroke-dasharray for percentage
        const circumference = 100; // Approximate
        const dashArray = `${percent}, ${circumference}`;
        circle.setAttribute('stroke-dasharray', dashArray);
    });

    // Update percentage text
    const percentTexts = document.querySelectorAll('.text-primary, [data-confidence-percent]');
    percentTexts.forEach(text => {
        if (text.textContent.includes('%')) {
            text.textContent = `${percent.toFixed(0)}%`;
        }
    });
}

/**
 * Update risk level display
 * @param {string} riskLevel - Risk level code
 * @param {string} riskLevelVi - Vietnamese risk level
 */
function updateRiskLevel(riskLevel, riskLevelVi) {
    const riskBadges = document.querySelectorAll('[data-risk-badge]');
    const badgeHTML = getRiskBadge(riskLevel, riskLevelVi);

    riskBadges.forEach(badge => {
        badge.innerHTML = badgeHTML;
    });

    // Update risk text
    updateElement('[data-risk-level]', riskLevelVi);
}

/**
 * Update recommendations section
 * @param {object} recommendations - Recommendations object
 */
function updateRecommendations(recommendations) {
    if (!recommendations) return;

    // Update description
    updateElement('[data-recommendation-description]', recommendations.description);

    // Update urgency
    updateElement('[data-recommendation-urgency]', recommendations.urgency);

    // Update actions list
    const actionsList = document.querySelector('[data-recommendation-actions]');
    if (actionsList && recommendations.actions) {
        actionsList.innerHTML = recommendations.actions.map(action => `
            <li class="flex items-start gap-3">
                <span class="material-symbols-outlined text-primary text-lg mt-0.5">check_circle</span>
                <span class="text-sm text-slate-700 dark:text-slate-300">${action}</span>
            </li>
        `).join('');
    }
}

/**
 * Update all predictions display
 * @param {object} predictions - All class predictions
 */
function updateAllPredictions(predictions) {
    const container = document.querySelector('[data-all-predictions]');
    if (!container || !predictions) return;

    // Get top 3 predictions
    const topPredictions = Object.entries(predictions)
        .slice(0, 3)
        .map(([classCode, confidence]) => ({
            classCode,
            diseaseNameVi: translateDiseaseName(classCode),
            confidence,
            confidencePercent: (confidence * 100).toFixed(1)
        }));

    // Create HTML
    container.innerHTML = topPredictions.map(pred => `
        <div class="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700">
            <span class="text-sm font-medium text-slate-700 dark:text-slate-300">${pred.diseaseNameVi}</span>
            <div class="flex items-center gap-2 flex-1 mx-4">
                <div class="flex-1 h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div class="h-full bg-primary rounded-full" style="width: ${pred.confidencePercent}%"></div>
                </div>
                <span class="text-xs font-bold text-slate-600 dark:text-slate-400">${pred.confidencePercent}%</span>
            </div>
        </div>
    `).join('');
}

/**
 * Setup result action buttons
 */
function setupResultActions() {
    // Save button
    const saveBtn = document.querySelector('[data-save-btn]');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            showSuccess('Kết quả đã được lưu');
        });
    }

    // Print button
    const printBtn = document.querySelector('[data-print-btn]');
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
        });
    }

    // Find clinic button
    const clinicBtn = document.querySelector('[data-clinic-btn]');
    if (clinicBtn) {
        clinicBtn.addEventListener('click', () => {
            showError('Chức năng tìm phòng khám đang được phát triển');
        });
    }
}
