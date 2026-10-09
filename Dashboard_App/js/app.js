// ⚙️ EPS Dashboard - Main Application Controller

// Single version stamp — bump this to invalidate every cached asset (scripts + view HTML)
const APP_VERSION = '20261009a';

// Base path of the app (works from /Dashboard_App/ or a custom sub-path)
const APP_BASE = (function () {
    const href = window.location.href.split('?')[0].split('#')[0];
    return href.substring(0, href.lastIndexOf('/') + 1);
})();

// Absolute RAW_Data folder — avoids relying on browser '..' normalisation,
// so it works on a local server AND on GitHub Pages project sub-paths.
// Deployment override: set window.EPS_DATA_BASE in js/config.js to load the CSVs
// from a separate host (keeps real customer data OUT of this repo).
const DATA_BASE = (function () {
    if (window.EPS_DATA_BASE) return window.EPS_DATA_BASE.replace(/\/?$/, '/');
    const href = window.location.href.split('?')[0].split('#')[0];
    const marker = '/Dashboard_App/';
    const i = href.indexOf(marker);
    if (i !== -1) return href.slice(0, i) + '/RAW_Data/';
    return href.substring(0, href.lastIndexOf('/') + 1) + '../RAW_Data/';
})();

// Detect the classic double-click (file://) mistake and explain it clearly
const IS_FILE_PROTOCOL = (window.location.protocol === 'file:');

// Show JS errors on screen instead of a silent blank page
window.addEventListener('error', function (e) {
    const box = document.getElementById('js-error-banner');
    if (!box) return;
    box.style.display = 'block';
    box.innerText = '⚠ JS Error: ' + (e.message || e.type) + (e.filename ? ' (' + e.filename.split('/').pop() + ':' + e.lineno + ')' : '');
});

const app = {
    init() {
        if (IS_FILE_PROTOCOL) {
            const b = document.getElementById('js-error-banner');
            if (b) {
                b.style.display = 'block';
                b.innerHTML = '⚠ Please open this dashboard through a local web server, not by double-clicking the file.<br>'
                    + 'Run: <code>cd "/home/jom/SynologyDrive/AI Dashboard" &amp;&amp; python3 -m http.server 8080</code><br>'
                    + 'then open <a href="http://localhost:8080/Dashboard_App/index.html">http://localhost:8080/Dashboard_App/index.html</a>';
            }
            return;
        }
        const user = auth.getCurrentUser();
        if (user) this.showDashboard(user);
        else this.showLogin();
    },
    login() {
        const userInp = document.getElementById('username').value;
        const passInp = document.getElementById('password').value;
        const errorEl = document.getElementById('login-error');
        if (!userInp) { errorEl.innerText = 'Please enter a username.'; return; }
        const result = auth.login(userInp, passInp);
        if (result.success) { errorEl.innerText = ''; this.showDashboard(result.user); }
        else { errorEl.innerText = result.message; }
    },
    logout() { auth.logout(); },
    showLogin() {
        document.getElementById('login-view').style.display = 'flex';
        document.getElementById('dashboard-layout').style.display = 'none';
    },
    showDashboard(user) {
        document.getElementById('login-view').style.display = 'none';
        document.getElementById('dashboard-layout').style.display = 'block';
        document.getElementById('current-user-name').innerText = user.name;
        document.getElementById('current-user-role').innerText = user.roleName;
        router.init(user);
    }
};

window.addEventListener('DOMContentLoaded', () => {
    try { app.init(); } catch (e) {
        const b = document.getElementById('js-error-banner');
        if (b) { b.style.display = 'block'; b.innerText = '⚠ Startup error: ' + e.message; }
    }
});
