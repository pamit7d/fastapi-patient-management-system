// notifications.js
// Usage: showToast('message', 'success'|'error')

const style = document.createElement('style');
style.innerHTML = `
.toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
}
.toast {
    min-width: 250px;
    background-color: #333;
    color: #fff;
    text-align: center;
    border-radius: 4px;
    padding: 16px;
    margin-bottom: 10px;
    opacity: 0;
    transition: opacity 0.3s, transform 0.3s;
    transform: translateY(-20px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.toast.show {
    opacity: 1;
    transform: translateY(0);
}
.toast.success { background-color: #10B981; }
.toast.error { background-color: #EF4444; }
.spinner {
    border: 2px solid #f3f3f3;
    border-top: 2px solid #3498db;
    border-radius: 50%;
    width: 16px;
    height: 16px;
    animation: spin 1s linear infinite;
    display: inline-block;
    vertical-align: middle;
    margin-right: 8px;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
`;
document.head.appendChild(style);

const container = document.createElement('div');
container.className = 'toast-container';
document.body.appendChild(container);

function showToast(message, type = 'info') {
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerText = message;
    container.appendChild(el);

    // Trigger animation
    requestAnimationFrame(() => el.classList.add('show'));

    setTimeout(() => {
        el.classList.remove('show');
        setTimeout(() => el.remove(), 300);
    }, 3000);
}

// Helper to wrap async functions with loading state
async function withLoading(btnId, fn) {
    const btn = document.getElementById(btnId);
    if (!btn) return fn();

    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<div class="spinner"></div> Processing...`;

    try {
        await fn();
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}
