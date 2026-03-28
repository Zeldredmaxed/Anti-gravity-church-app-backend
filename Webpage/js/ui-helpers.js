/**
 * Shepherd ChMS — UI Helpers
 * Toast notifications, loading states, formatters, and chart builders.
 */
const ShepherdUI = (() => {

    // ══════════════════════════════════════════
    //  TOAST NOTIFICATIONS
    // ══════════════════════════════════════════
    function _ensureToastContainer() {
        let c = document.getElementById('shepherd-toast-container');
        if (!c) {
            c = document.createElement('div');
            c.id = 'shepherd-toast-container';
            c.style.cssText = `
                position: fixed; top: 24px; right: 24px; z-index: 9999;
                display: flex; flex-direction: column; gap: 10px;
                pointer-events: none;
            `;
            document.body.appendChild(c);
        }
        return c;
    }

    const TOAST_ICONS = {
        success: 'fa-solid fa-circle-check',
        error:   'fa-solid fa-circle-xmark',
        info:    'fa-solid fa-circle-info',
        warning: 'fa-solid fa-triangle-exclamation',
    };
    const TOAST_COLORS = {
        success: '#166534',
        error:   '#991b1b',
        info:    '#1e40af',
        warning: '#854d0e',
    };
    const TOAST_BGS = {
        success: 'rgba(220, 252, 231, 0.95)',
        error:   'rgba(254, 226, 226, 0.95)',
        info:    'rgba(219, 234, 254, 0.95)',
        warning: 'rgba(254, 249, 195, 0.95)',
    };

    function showToast(message, type = 'info', duration = 4000) {
        const container = _ensureToastContainer();
        const toast = document.createElement('div');
        toast.style.cssText = `
            background: ${TOAST_BGS[type] || TOAST_BGS.info};
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.6);
            border-radius: 14px;
            padding: 14px 20px;
            display: flex; align-items: center; gap: 10px;
            font-size: 13px; font-weight: 500; font-family: 'Inter', sans-serif;
            color: ${TOAST_COLORS[type] || TOAST_COLORS.info};
            box-shadow: 0 8px 32px rgba(0,0,0,0.08);
            pointer-events: auto;
            transform: translateX(120%);
            transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s;
            max-width: 380px;
        `;
        toast.innerHTML = `<i class="${TOAST_ICONS[type] || TOAST_ICONS.info}" style="font-size:16px;"></i><span>${message}</span>`;
        container.appendChild(toast);

        requestAnimationFrame(() => { toast.style.transform = 'translateX(0)'; });

        setTimeout(() => {
            toast.style.transform = 'translateX(120%)';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 400);
        }, duration);
    }

    // ══════════════════════════════════════════
    //  LOADING / SKELETON STATES
    // ══════════════════════════════════════════
    function showSpinner(container) {
        if (typeof container === 'string') container = document.querySelector(container);
        if (!container) return;
        container.dataset.originalHtml = container.innerHTML;
        container.innerHTML = `
            <div style="display:flex;justify-content:center;align-items:center;padding:40px;opacity:0.5;">
                <i class="fa-solid fa-circle-notch fa-spin" style="font-size:24px;color:var(--accent-yellow);"></i>
                <span style="margin-left:12px;font-size:13px;color:var(--text-muted);">Loading...</span>
            </div>
        `;
    }

    function hideSpinner(container) {
        if (typeof container === 'string') container = document.querySelector(container);
        if (!container) return;
        // Don't restore — the caller will populate dynamic content
    }

    function showSkeletonRows(tbody, cols = 6, rows = 5) {
        if (typeof tbody === 'string') tbody = document.querySelector(tbody);
        if (!tbody) return;
        let html = '';
        for (let r = 0; r < rows; r++) {
            html += '<tr>';
            for (let c = 0; c < cols; c++) {
                html += `<td><div style="height:14px;background:rgba(0,0,0,0.06);border-radius:8px;animation:shimmer 1.5s infinite;"></div></td>`;
            }
            html += '</tr>';
        }
        tbody.innerHTML = html;
    }

    // Inject shimmer keyframes if not present
    if (!document.getElementById('shepherd-shimmer-style')) {
        const style = document.createElement('style');
        style.id = 'shepherd-shimmer-style';
        style.textContent = `
            @keyframes shimmer {
                0% { opacity: 0.5; }
                50% { opacity: 1; }
                100% { opacity: 0.5; }
            }
        `;
        document.head.appendChild(style);
    }

    // ══════════════════════════════════════════
    //  FORMATTERS
    // ══════════════════════════════════════════
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount);
    }

    function formatCurrencyFull(amount) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
    }

    function formatNumber(n) {
        return new Intl.NumberFormat('en-US').format(n);
    }

    function formatDate(dateStr) {
        if (!dateStr) return '—';
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    function formatRelativeTime(dateStr) {
        if (!dateStr) return '';
        const diff = Date.now() - new Date(dateStr).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return 'Just now';
        if (mins < 60) return `${mins}m ago`;
        const hours = Math.floor(mins / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        if (days < 7) return `${days}d ago`;
        return formatDate(dateStr);
    }

    // ══════════════════════════════════════════
    //  SVG LINE CHART BUILDER
    // ══════════════════════════════════════════
    /**
     * Build a line chart SVG inside a container.
     * @param {Array<{date: string, value: number}>} data
     * @param {Element|string} container - target element or selector
     * @param {object} opts - { width, height, color, gradientId }
     */
    function buildLineChart(data, container, opts = {}) {
        if (typeof container === 'string') container = document.querySelector(container);
        if (!container || !data || data.length === 0) {
            if (container) container.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);font-size:13px;">No data available</div>';
            return;
        }

        const w = opts.width || 800;
        const h = opts.height || 100;
        const color = opts.color || '#dcb34a';
        const gId = opts.gradientId || 'chart-gradient';

        const maxVal = Math.max(...data.map(d => d.value)) || 1;
        const points = data.map((d, i) => ({
            x: (i / (data.length - 1 || 1)) * w,
            y: h - (d.value / maxVal) * (h * 0.85) - 5,
        }));

        const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
        const fillPath = linePath + ` L${w},${h} L0,${h} Z`;

        // Find the highest point for the highlight dot
        const peakIdx = data.reduce((mi, d, i, a) => d.value > a[mi].value ? i : mi, 0);

        container.innerHTML = `
            <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
                <defs>
                    <linearGradient id="${gId}" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="0%" stop-color="${color}" stop-opacity="0.4"/>
                        <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
                    </linearGradient>
                </defs>
                <path class="chart-fill" d="${fillPath}" fill="url(#${gId})" opacity="0.5"></path>
                <path class="chart-line" d="${linePath}" fill="none" stroke="${color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></path>
                <circle cx="${points[peakIdx].x.toFixed(1)}" cy="${points[peakIdx].y.toFixed(1)}" r="4" fill="white" stroke="${color}" stroke-width="3"></circle>
            </svg>
        `;
    }

    // ══════════════════════════════════════════
    //  BAR CHART BUILDER
    // ══════════════════════════════════════════
    function buildBarChart(data, container, opts = {}) {
        if (typeof container === 'string') container = document.querySelector(container);
        if (!container || !data || data.length === 0) {
            if (container) container.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);font-size:13px;">No data available</div>';
            return;
        }

        const color = opts.color || 'rgba(0,0,0,0.1)';
        const highlightColor = opts.highlightColor || 'var(--dark-card-bg)';
        const maxVal = Math.max(...data.map(d => d.value)) || 1;
        const peakIdx = data.reduce((mi, d, i, a) => d.value > a[mi].value ? i : mi, 0);

        container.innerHTML = data.map((d, i) => {
            const pct = ((d.value / maxVal) * 100).toFixed(0);
            const isHighlight = i === peakIdx;
            return `
                <div class="bar-wrapper">
                    <div class="bar${isHighlight ? ' highlight' : ''}" style="height:${pct}%;${!isHighlight ? `background:${color};` : `background:${highlightColor};`}" title="${d.value}"></div>
                    <span class="bar-label" ${isHighlight ? 'style="color:var(--text-dark);font-weight:600;"' : ''}>${d.date}</span>
                </div>
            `;
        }).join('');
    }

    // ══════════════════════════════════════════
    //  DONUT CHART BUILDER
    // ══════════════════════════════════════════
    function buildDonutChart(segments, container, opts = {}) {
        if (typeof container === 'string') container = document.querySelector(container);
        if (!container || !segments || segments.length === 0) return;

        const colors = opts.colors || ['#1d4ed8', '#f59e0b', '#16a34a', '#dc2626', '#8b5cf6'];
        const total = segments.reduce((s, seg) => s + seg.count, 0) || 1;

        let gradientParts = [];
        let cumPct = 0;
        segments.forEach((seg, i) => {
            const pct = (seg.count / total) * 100;
            const c = colors[i % colors.length];
            gradientParts.push(`${c} ${cumPct.toFixed(1)}% ${(cumPct + pct).toFixed(1)}%`);
            cumPct += pct;
        });

        const legendHtml = segments.map((seg, i) =>
            `<div class="legend-item"><div class="legend-dot" style="background:${colors[i % colors.length]};"></div>${seg.status} (${seg.count})</div>`
        ).join('');

        container.innerHTML = `
            <div class="donut-chart" style="background:conic-gradient(${gradientParts.join(', ')});">
                <div class="donut-inner">${total}</div>
            </div>
            <div class="donut-legend">${legendHtml}</div>
        `;
    }

    // ══════════════════════════════════════════
    //  HEALTH SCORE HELPERS
    // ══════════════════════════════════════════
    function healthScoreClass(score) {
        if (score >= 70) return 'green';
        if (score >= 40) return 'yellow';
        return 'red';
    }

    function healthScoreLabel(score) {
        if (score >= 70) return 'Engaged';
        if (score >= 40) return 'Inconsistent';
        return 'At Risk';
    }

    return {
        showToast,
        showSpinner,
        hideSpinner,
        showSkeletonRows,
        formatCurrency,
        formatCurrencyFull,
        formatNumber,
        formatDate,
        formatRelativeTime,
        buildLineChart,
        buildBarChart,
        buildDonutChart,
        healthScoreClass,
        healthScoreLabel,
    };
})();
