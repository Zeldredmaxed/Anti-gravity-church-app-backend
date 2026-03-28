/**
 * Shepherd ChMS — API Client
 * Central fetch wrapper with JWT auth, token refresh, and error handling.
 */
const ShepherdAPI = (() => {
    // ── Config ──
    const API_BASE = window.SHEPHERD_API_BASE || 'https://anti-gravity-church-app-backend-production.up.railway.app/api/v1';

    // ── Token helpers ──
    function getToken() { return localStorage.getItem('shepherd_access_token'); }
    function getRefreshToken() { return localStorage.getItem('shepherd_refresh_token'); }
    function setTokens(access, refresh) {
        localStorage.setItem('shepherd_access_token', access);
        if (refresh) localStorage.setItem('shepherd_refresh_token', refresh);
    }
    function clearTokens() {
        localStorage.removeItem('shepherd_access_token');
        localStorage.removeItem('shepherd_refresh_token');
        localStorage.removeItem('shepherd_user');
    }

    // ── Core fetch ──
    async function request(method, path, body = null, isRetry = false) {
        const url = `${API_BASE}${path}`;
        const headers = { 'Content-Type': 'application/json' };
        const token = getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const opts = { method, headers };
        if (body && method !== 'GET') opts.body = JSON.stringify(body);

        let res;
        try {
            res = await fetch(url, opts);
        } catch (err) {
            throw new Error(`Network error: ${err.message}`);
        }

        // ── 401 → Attempt token refresh ──
        if (res.status === 401 && !isRetry) {
            const refreshed = await tryRefresh();
            if (refreshed) return request(method, path, body, true);
            // Refresh failed — redirect to login
            clearTokens();
            if (!window.location.pathname.includes('index')) {
                window.location.href = 'index.html';
            }
            throw new Error('Session expired');
        }

        // ── Parse response ──
        const text = await res.text();
        let data;
        try { data = JSON.parse(text); } catch { data = text; }

        if (!res.ok) {
            const msg = data?.detail || data?.message || `Error ${res.status}`;
            throw new Error(msg);
        }
        return data;
    }

    async function tryRefresh() {
        const refresh = getRefreshToken();
        if (!refresh) return false;
        try {
            const res = await fetch(`${API_BASE}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refresh }),
            });
            if (!res.ok) return false;
            const data = await res.json();
            setTokens(data.access_token, data.refresh_token || refresh);
            return true;
        } catch {
            return false;
        }
    }

    // ── Public API ──
    return {
        API_BASE,
        get:    (path)       => request('GET', path),
        post:   (path, body) => request('POST', path, body),
        put:    (path, body) => request('PUT', path, body),
        patch:  (path, body) => request('PATCH', path, body),
        delete: (path)       => request('DELETE', path),
        setTokens,
        clearTokens,
        getToken,
    };
})();
