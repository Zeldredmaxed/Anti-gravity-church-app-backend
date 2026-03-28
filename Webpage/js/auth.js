/**
 * Shepherd ChMS — Auth Module
 * Login, logout, session management, and header injection.
 */
const ShepherdAuth = (() => {
    let _cachedUser = null;

    function isLoggedIn() {
        return !!ShepherdAPI.getToken();
    }

    async function login(email, password) {
        const data = await ShepherdAPI.post('/auth/login', { email, password });
        ShepherdAPI.setTokens(data.access_token, data.refresh_token);
        _cachedUser = null; // force re-fetch
        return data;
    }

    function logout() {
        ShepherdAPI.clearTokens();
        _cachedUser = null;
        window.location.href = 'index.html';
    }

    async function getCurrentUser(forceRefresh = false) {
        if (_cachedUser && !forceRefresh) return _cachedUser;
        // Try cache first
        const cached = localStorage.getItem('shepherd_user');
        if (cached && !forceRefresh) {
            _cachedUser = JSON.parse(cached);
            return _cachedUser;
        }
        try {
            const user = await ShepherdAPI.get('/auth/me');
            _cachedUser = user;
            localStorage.setItem('shepherd_user', JSON.stringify(user));
            return user;
        } catch (err) {
            console.warn('Failed to fetch current user:', err);
            return null;
        }
    }

    /**
     * Inject user data into the global header (avatar + name).
     * Looks for .avatar img and optionally a .user-name element.
     */
    async function injectUserIntoHeader() {
        if (!isLoggedIn()) return;
        const user = await getCurrentUser();
        if (!user) return;

        // Update avatar
        const avatarEls = document.querySelectorAll('header .avatar');
        avatarEls.forEach(el => {
            if (user.avatar_url) el.src = user.avatar_url;
            el.alt = user.full_name || 'Profile';
        });

        // Update name if element exists
        const nameEl = document.querySelector('.user-display-name');
        if (nameEl && user.full_name) nameEl.textContent = user.full_name;
    }

    /**
     * Guard — call on every page load (except login).
     * Redirects to login if no valid session.
     */
    function requireAuth() {
        if (!isLoggedIn()) {
            window.location.href = 'index.html';
            return false;
        }
        return true;
    }

    return {
        isLoggedIn,
        login,
        logout,
        getCurrentUser,
        injectUserIntoHeader,
        requireAuth,
    };
})();
