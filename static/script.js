// --- Constants ---
const HTML = document.documentElement;
const themeToggle = document.getElementById('theme-toggle');
const form = document.getElementById('download-form');
const submitBtn = document.getElementById('submit-btn');
const statusBar = document.getElementById('status-bar');
const statusMessage = document.getElementById('status-message');

// Progress Bar Elements
const downloadProgressContainer = document.getElementById('download-progress-container');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');


// --- Helper Functions ---

function updateStatus(message, type) {
    statusBar.classList.remove('hidden', 'status-success', 'status-error');
    statusBar.classList.add(`status-${type}`);
    statusMessage.textContent = message;
    
    // Auto-hide status bar after 5 seconds
    setTimeout(() => {
        statusBar.classList.add('hidden');
    }, 5000);
}

function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    if (isLoading) {
        submitBtn.classList.add('is-loading');
    } else {
        submitBtn.classList.remove('is-loading');
    }
}

// --- Theme Toggling Logic ---

function initializeTheme() {
    const storedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (storedTheme === 'dark' || (!storedTheme && systemPrefersDark)) {
        HTML.classList.add('dark-mode');
    }
}

function toggleTheme() {
    HTML.classList.toggle('dark-mode');
    if (HTML.classList.contains('dark-mode')) {
        localStorage.setItem('theme', 'dark');
    } else {
        localStorage.setItem('theme', 'light');
    }
}

document.addEventListener('DOMContentLoaded', initializeTheme);
themeToggle.addEventListener('click', toggleTheme);


// --- Form Submission Logic (Local Download) ---
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    setLoading(true);
    
    const formData = new FormData(form);

    // --- PROGRESS BAR INITIALIZATION (Simulated) ---
    downloadProgressContainer.classList.remove('hidden');
    progressBar.style.width = '10%'; 
    progressText.textContent = 'Queueing download task on the Raspberry Pi...';
    statusBar.classList.add('hidden'); 


    try {
        const response = await fetch('/download', {
            method: 'POST',
            body: formData 
        });
        
        const result = await response.json();

        // --- PROGRESS BAR UPDATE ---
        if (response.ok) {
            // Success (queued)
            progressBar.style.width = '100%'; 
            progressText.textContent = 'Task Queued Successfully!';
            updateStatus(result.message, 'success');
            form.reset();
        } else {
            // Error (e.g., 400 for bad URL)
            progressBar.style.width = '0%';
            progressText.textContent = 'Download Failed.';
            updateStatus(result.message || 'An unknown error occurred on the server.', 'error');
        }

    } catch (error) {
        console.error('Fetch error:', error);
        progressBar.style.width = '0%';
        updateStatus("Network connection failed or server is unreachable.", 'error');
    } finally {
        setLoading(false);
        // Hide progress container after a short delay
        setTimeout(() => {
            downloadProgressContainer.classList.add('hidden');
        }, 3000); 
    }
});
