/**
 * API Client — Centralized fetch wrapper with JWT auth
 */
const API_BASE = 'https://anti-gravity-church-app-backend-production.up.railway.app/api/v1';

function getToken() {
    return localStorage.getItem('token');
}

function getUser() {
    try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch { return {}; }
}

async function api(path, opts = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...(getToken() ? { 'Authorization': `Bearer ${getToken()}` } : {}),
        ...(opts.headers || {})
    };

    const res = await fetch(`${API_BASE}${path}`, {
        ...opts,
        headers,
        body: opts.body ? (typeof opts.body === 'string' ? opts.body : JSON.stringify(opts.body)) : undefined
    });

    if (res.status === 401) {
        localStorage.clear();
        window.location.href = 'login.html';
        return;
    }

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `API error ${res.status}`);
    return data;
}

function apiGet(path) { return api(path); }
function apiPost(path, body) { return api(path, { method: 'POST', body }); }
function apiPut(path, body) { return api(path, { method: 'PUT', body }); }
function apiDelete(path) { return api(path, { method: 'DELETE' }); }

function logout() {
    localStorage.clear();
    window.location.href = 'login.html';
}

function timeAgo(dateStr) {
    const now = Date.now();
    const d = new Date(dateStr).getTime();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    return new Date(dateStr).toLocaleDateString();
}

function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric'
    });
}

function formatDateTime(dateStr) {
    return new Date(dateStr).toLocaleString('en-US', {
        month: 'short', day: 'numeric',
        hour: 'numeric', minute: '2-digit'
    });
}
