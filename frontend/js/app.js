/**
 * Core App Logic
 * Navigation, theme toggle, and shared functionality
 */

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    console.log('MedAI Frontend initialized');

    // Setup navigation
    setupNavigation();

    // Setup theme toggle (if exists)
    setupThemeToggle();

    // Check backend health
    checkBackendHealth();
});

/**
 * Setup navigation handlers
 */
function setupNavigation() {
    // Get all navigation links
    const navLinks = document.querySelectorAll('a[href]');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');

        // Update relative links to work with project structure
        if (href && !href.startsWith('http') && !href.startsWith('#')) {
            // Make sure links work from different page levels
            if (href.startsWith('pages/')) {
                // Already correct from index.html
            } else if (href === 'index.html' || href === '/') {
                // Going back to index from pages
                const currentPath = window.location.pathname;
                if (currentPath.includes('/pages/')) {
                    link.setAttribute('href', '../index.html');
                }
            }
        }
    });
}

/**
 * Setup theme toggle functionality
 */
function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');

    if (!themeToggle) return;

    // Check saved theme preference
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.classList.toggle('dark', currentTheme === 'dark');

    // Toggle theme on click
    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

/**
 * Check backend API health
 */
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log('✓ Backend API is healthy:', data);

            if (!data.model_loaded) {
                console.warn('⚠ AI Model not loaded on backend');
            }
        } else {
            console.warn('⚠ Backend API health check failed');
        }
    } catch (error) {
        console.error('✗ Cannot connect to backend API:', error.message);
        console.error('Make sure backend is running at:', API_CONFIG.BASE_URL);
    }
}

/**
 * Navigate to a page with optional state
 * @param {string} url - Page URL
 * @param {object} state - State object to pass
 */
function navigateTo(url, state = {}) {
    if (Object.keys(state).length > 0) {
        // Store state for next page
        sessionStorage.setItem('navigationState', JSON.stringify(state));
    }
    window.location.href = url;
}

/**
 * Get navigation state from previous page
 * @returns {object} State object or null
 */
function getNavigationState() {
    try {
        const state = sessionStorage.getItem('navigationState');
        if (state) {
            sessionStorage.removeItem('navigationState');
            return JSON.parse(state);
        }
    } catch (e) {
        console.error('Failed to get navigation state:', e);
    }
    return null;
}
