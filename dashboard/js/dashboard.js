/**
 * Church Dashboard — Main SPA Controller
 * Handles view switching, data loading, and rendering
 * Uses Lucide icons for professional UI
 */

// ── Icon helper — generates Lucide-compatible inline SVG references ──
function icon(name, size = 18) {
    return `<i data-lucide="${name}" style="width:${size}px;height:${size}px;display:inline-flex;vertical-align:middle"></i>`;
}

// Reinitialize Lucide icons after dynamic content renders
function refreshIcons() {
    if (window.lucide) lucide.createIcons();
}

let currentView = 'overview';

// ── Init ──
(function init() {
    if (!getToken()) { window.location.href = 'index.html'; return; }
    const user = getUser();
    document.getElementById('churchName').textContent = 'Church Dashboard';
    document.getElementById('userRole').textContent = (user.role || 'member').toUpperCase();
    document.getElementById('userName').textContent = user.full_name || 'User';
    document.getElementById('userEmail').textContent = user.email || '';
    document.getElementById('userAvatar').textContent = (user.full_name || 'U')[0].toUpperCase();
    switchView('overview');
    loadNotificationCount();
})();

function switchView(view) {
    currentView = view;
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.toggle('active', el.dataset.view === view);
    });
    const titles = {
        overview: 'Overview', members: 'Members', events: 'Events',
        prayers: 'Prayer Wall', feed: 'Feed', shorts: 'Shorts',
        giving: 'Giving & Finance', notifications: 'Notifications'
    };
    document.getElementById('pageTitle').textContent = titles[view] || 'Dashboard';
    document.getElementById('sidebar').classList.remove('open');
    const area = document.getElementById('contentArea');
    area.innerHTML = '<div class="skeleton" style="height:200px;margin-bottom:16px"></div><div class="skeleton" style="height:300px"></div>';
    const renderers = {
        overview: renderOverview, members: renderMembers, events: renderEvents,
        prayers: renderPrayers, feed: renderFeed, shorts: renderShorts,
        giving: renderGiving, notifications: renderNotifications
    };
    if (renderers[view]) renderers[view]();
}

// ── OVERVIEW ──────────────────
async function renderOverview() {
    const area = document.getElementById('contentArea');
    try {
        const [analytics, engagement, growth] = await Promise.all([
            apiGet('/reports/analytics/overview'),
            apiGet('/reports/analytics/engagement'),
            apiGet('/reports/analytics/growth')
        ]);

        area.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card purple">
                    <div class="stat-icon">${icon('users', 22)}</div>
                    <div class="stat-value">${analytics.total_members}</div>
                    <div class="stat-label">Total Members</div>
                    <div class="stat-trend up">+${analytics.new_members_this_month} this month</div>
                </div>
                <div class="stat-card teal">
                    <div class="stat-icon">${icon('wallet', 22)}</div>
                    <div class="stat-value">$${Number(analytics.total_giving_this_month).toLocaleString()}</div>
                    <div class="stat-label">Giving This Month</div>
                </div>
                <div class="stat-card gold">
                    <div class="stat-icon">${icon('calendar-days', 22)}</div>
                    <div class="stat-value">${analytics.upcoming_events}</div>
                    <div class="stat-label">Upcoming Events</div>
                </div>
                <div class="stat-card pink">
                    <div class="stat-icon">${icon('hand-heart', 22)}</div>
                    <div class="stat-value">${analytics.active_prayer_requests}</div>
                    <div class="stat-label">Prayer Requests</div>
                </div>
            </div>

            <div class="grid-2">
                <!-- Engagement Score -->
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">${icon('activity', 16)} Engagement Score</div>
                    </div>
                    <div class="panel-body" style="text-align:center;padding:28px">
                        <div class="engagement-ring" style="--score-deg: ${analytics.engagement_score * 3.6}deg">
                            ${analytics.engagement_score}
                        </div>
                        <div style="color:var(--text-secondary);font-size:13px">
                            Community Health Index
                        </div>
                        <div style="display:flex;justify-content:center;gap:20px;margin-top:16px">
                            <div style="text-align:center">
                                <div style="font-size:18px;font-weight:700">${analytics.posts_this_month}</div>
                                <div style="font-size:11px;color:var(--text-muted)">Posts</div>
                            </div>
                            <div style="text-align:center">
                                <div style="font-size:18px;font-weight:700">${analytics.messages_this_month}</div>
                                <div style="font-size:11px;color:var(--text-muted)">Messages</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Growth Funnel -->
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">${icon('trending-up', 16)} Growth Funnel</div>
                    </div>
                    <div class="panel-body">
                        ${renderFunnel(growth.funnel)}
                        <div style="margin-top:16px">
                            ${(growth.monthly_growth || []).slice(-3).map(m =>
                                `<div style="display:flex;justify-content:space-between;padding:6px 0;font-size:13px;border-bottom:1px solid var(--border)">
                                    <span style="color:var(--text-secondary)">${m.month}</span>
                                    <span style="font-weight:600;color:var(--success)">+${m.new_members}</span>
                                </div>`
                            ).join('')}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Weekly Engagement -->
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">${icon('bar-chart-3', 16)} Weekly Engagement</div>
                </div>
                <div class="panel-body">
                    <table class="data-table">
                        <thead><tr>
                            <th>Period</th><th>Posts</th><th>Comments</th><th>Prayers</th>
                        </tr></thead>
                        <tbody>
                            ${(engagement.weekly_engagement || []).map(w =>
                                `<tr>
                                    <td>${w.week} <span style="color:var(--text-muted);font-size:11px">(${w.start_date})</span></td>
                                    <td><span class="badge badge-purple">${w.posts}</span></td>
                                    <td><span class="badge badge-teal">${w.comments}</span></td>
                                    <td><span class="badge badge-gold">${w.prayer_requests}</span></td>
                                </tr>`
                            ).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        refreshIcons();
    } catch (e) {
        area.innerHTML = `<div class="empty-state"><div class="empty-state-icon">${icon('bar-chart-3', 40)}</div>
            <div class="empty-state-title">Could not load analytics</div>
            <div class="empty-state-text">${e.message}</div></div>`;
        refreshIcons();
    }
}

function renderFunnel(funnel) {
    if (!funnel) return '';
    const total = Math.max(funnel.visitors + funnel.prospects + funnel.active_members + funnel.inactive_members, 1);
    const items = [
        { label: 'Visitors', value: funnel.visitors, color: 'var(--accent-light)' },
        { label: 'Prospects', value: funnel.prospects, color: 'var(--gold)' },
        { label: 'Active Members', value: funnel.active_members, color: 'var(--success)' },
        { label: 'Inactive', value: funnel.inactive_members, color: 'var(--text-muted)' },
    ];
    return items.map(i => `
        <div style="margin-bottom:10px">
            <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                <span style="color:var(--text-secondary)">${i.label}</span>
                <span style="font-weight:700">${i.value}</span>
            </div>
            <div style="height:6px;background:var(--border);border-radius:3px;overflow:hidden">
                <div style="height:100%;width:${Math.round(i.value/total*100)}%;background:${i.color};border-radius:3px;transition:width 0.5s"></div>
            </div>
        </div>
    `).join('');
}

// ── MEMBERS ──────────────────
async function renderMembers() {
    const area = document.getElementById('contentArea');
    try {
        const resp = await apiGet('/members');
        const members = Array.isArray(resp) ? resp : (resp.items || []);
        const total = Array.isArray(resp) ? resp.length : (resp.total || members.length);
        area.innerHTML = `
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">${icon('users', 16)} All Members (${total})</div>
                    <div class="panel-actions">
                        <button class="btn btn-primary" onclick="showAddMemberModal()">+ Add Member</button>
                    </div>
                </div>
                ${members.length === 0
                    ? `<div class="empty-state"><div class="empty-state-icon">${icon('users', 40)}</div>
                        <div class="empty-state-title">No members yet</div>
                        <div class="empty-state-text">Add your first church member to get started</div></div>`
                    : `<table class="data-table">
                        <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Status</th><th>Joined</th></tr></thead>
                        <tbody>${members.map(m => `
                            <tr>
                                <td style="font-weight:600;color:var(--text-primary)">${m.first_name} ${m.last_name}</td>
                                <td>${m.email || '—'}</td>
                                <td>${m.phone || '—'}</td>
                                <td><span class="badge ${m.membership_status === 'active' ? 'badge-success' : m.membership_status === 'visitor' ? 'badge-gold' : 'badge-purple'}">${m.membership_status || 'member'}</span></td>
                                <td style="color:var(--text-muted)">${m.join_date ? formatDate(m.join_date) : '—'}</td>
                            </tr>`).join('')}
                        </tbody>
                    </table>`
                }
            </div>
        `;
        refreshIcons();
    } catch (e) {
        area.innerHTML = `<div class="empty-state"><div class="empty-state-icon">${icon('alert-circle', 40)}</div>
            <div class="empty-state-title">${e.message}</div></div>`;
        refreshIcons();
    }
}

function showAddMemberModal() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-header"><h3>Add New Member</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()"><i data-lucide="x" style="width:18px;height:18px"></i></button></div>
            <div class="modal-body">
                <div class="grid-2">
                    <div class="field"><label>First Name</label><input id="mFirst" placeholder="John"></div>
                    <div class="field"><label>Last Name</label><input id="mLast" placeholder="Smith"></div>
                </div>
                <div class="field"><label>Email</label><input id="mEmail" type="email" placeholder="john@example.com"></div>
                <div class="field"><label>Phone</label><input id="mPhone" placeholder="(555) 123-4567"></div>
                <div class="field"><label>Status</label>
                    <select id="mStatus">
                        <option value="visitor">Visitor</option>
                        <option value="prospect">Prospect</option>
                        <option value="active" selected>Active Member</option>
                    </select>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="addMember()">Add Member</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);
    refreshIcons();
}

async function addMember() {
    try {
        await apiPost('/members', {
            first_name: document.getElementById('mFirst').value,
            last_name: document.getElementById('mLast').value,
            email: document.getElementById('mEmail').value || null,
            phone: document.getElementById('mPhone').value || null,
            membership_status: document.getElementById('mStatus').value
        });
        document.querySelector('.modal-overlay')?.remove();
        renderMembers();
    } catch (e) { alert(e.message); }
}

// ── EVENTS ──────────────────
async function renderEvents() {
    const area = document.getElementById('contentArea');
    try {
        const events = await apiGet('/events');
        area.innerHTML = `
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">${icon('calendar-days', 16)} Events</div>
                    <div class="panel-actions">
                        <button class="btn btn-primary" onclick="showAddEventModal()">+ Create Event</button>
                    </div>
                </div>
                ${events.length === 0
                    ? `<div class="empty-state"><div class="empty-state-icon">${icon('calendar-days', 40)}</div>
                        <div class="empty-state-title">No events</div>
                        <div class="empty-state-text">Create an event and manage RSVPs</div></div>`
                    : events.map(ev => `
                        <div class="list-item">
                            <div class="list-item-icon" style="background:rgba(108,92,231,0.15)">${icon('calendar-check', 20)}</div>
                            <div class="list-item-content">
                                <div class="list-item-title">${ev.title}</div>
                                <div class="list-item-sub">${ev.description || ''}</div>
                                <div class="list-item-meta">
                                    ${icon('map-pin', 12)} ${ev.location || 'TBD'} &nbsp;&middot;&nbsp;
                                    ${icon('clock', 12)} ${formatDateTime(ev.start_datetime)} &nbsp;&middot;&nbsp;
                                    ${ev.max_capacity ? `${icon('users', 12)} ${ev.rsvp_count ?? 0}/${ev.max_capacity}` : ''}
                                </div>
                            </div>
                            <div class="list-item-actions">
                                <span class="badge ${ev.is_cancelled ? 'badge-danger' : 'badge-success'}">
                                    ${ev.is_cancelled ? 'Cancelled' : ev.event_type}
                                </span>
                            </div>
                        </div>
                    `).join('')
                }
            </div>
        `;
        refreshIcons();
    } catch (e) {
        area.innerHTML = `<div class="empty-state"><div class="empty-state-icon">${icon('alert-circle', 40)}</div>
            <div class="empty-state-title">${e.message}</div></div>`;
        refreshIcons();
    }
}

function showAddEventModal() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 16);
    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-header"><h3>Create Event</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()"><i data-lucide="x" style="width:18px;height:18px"></i></button></div>
            <div class="modal-body">
                <div class="field"><label>Title</label><input id="evTitle" placeholder="Sunday Service"></div>
                <div class="field"><label>Description</label><textarea id="evDesc" placeholder="Event details..."></textarea></div>
                <div class="grid-2">
                    <div class="field"><label>Type</label>
                        <select id="evType">
                            <option value="service">Service</option>
                            <option value="event">Event</option>
                            <option value="meeting">Meeting</option>
                            <option value="conference">Conference</option>
                        </select></div>
                    <div class="field"><label>Location</label><input id="evLoc" placeholder="Main Sanctuary"></div>
                </div>
                <div class="grid-2">
                    <div class="field"><label>Start Date/Time</label><input id="evStart" type="datetime-local" value="${tomorrow}"></div>
                    <div class="field"><label>Max Capacity</label><input id="evCap" type="number" placeholder="200"></div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="addEvent()">Create Event</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);
    refreshIcons();
}

async function addEvent() {
    try {
        await apiPost('/events', {
            title: document.getElementById('evTitle').value,
            description: document.getElementById('evDesc').value,
            event_type: document.getElementById('evType').value,
            location: document.getElementById('evLoc').value,
            start_datetime: new Date(document.getElementById('evStart').value).toISOString(),
            max_capacity: parseInt(document.getElementById('evCap').value) || null,
            registration_required: true
        });
        document.querySelector('.modal-overlay')?.remove();
        renderEvents();
    } catch (e) { alert(e.message); }
}

// ── PRAYER WALL ──────────────────
async function renderPrayers() {
    const area = document.getElementById('contentArea');
    try {
        const prayers = await apiGet('/prayers');
        area.innerHTML = `
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">${icon('hand-heart', 16)} Prayer Wall</div>
                    <div class="panel-actions">
                        <button class="btn btn-primary" onclick="showAddPrayerModal()">+ Submit Prayer</button>
                    </div>
                </div>
                ${prayers.length === 0
                    ? `<div class="empty-state"><div class="empty-state-icon">${icon('hand-heart', 40)}</div>
                        <div class="empty-state-title">No prayer requests</div>
                        <div class="empty-state-text">Be the first to share a prayer need</div></div>`
                    : prayers.map(p => `
                        <div class="list-item">
                            <div class="list-item-icon" style="background:${p.is_urgent ? 'rgba(255,107,107,0.15)' : 'rgba(240,192,64,0.15)'}">
                                ${p.is_urgent ? icon('flame', 20) : icon('hand-heart', 20)}
                            </div>
                            <div class="list-item-content">
                                <div class="list-item-title">
                                    ${p.title}
                                    ${p.is_answered ? '<span class="badge badge-success" style="margin-left:8px">Answered</span>' : ''}
                                    ${p.is_urgent ? '<span class="badge badge-danger" style="margin-left:8px">Urgent</span>' : ''}
                                </div>
                                <div class="list-item-sub">${p.description || ''}</div>
                                <div class="list-item-meta">
                                    By ${p.author_name || 'Anonymous'} &nbsp;&middot;&nbsp;
                                    ${p.prayed_count || 0} prayed &nbsp;&middot;&nbsp;
                                    ${p.category || 'general'} &nbsp;&middot;&nbsp;
                                    ${timeAgo(p.created_at)}
                                </div>
                            </div>
                            <div class="list-item-actions">
                                <button class="btn btn-sm btn-secondary" onclick="prayFor('${p.id}')">Pray</button>
                            </div>
                        </div>
                    `).join('')
                }
            </div>
        `;
        refreshIcons();
    } catch (e) {
        area.innerHTML = `<div class="empty-state"><div class="empty-state-icon">${icon('alert-circle', 40)}</div>
            <div class="empty-state-title">${e.message}</div></div>`;
        refreshIcons();
    }
}

async function prayFor(id) {
    try { await apiPost(`/prayers/${id}/pray`); renderPrayers(); } catch (e) { alert(e.message); }
}

function showAddPrayerModal() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-header"><h3>Submit Prayer Request</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()"><i data-lucide="x" style="width:18px;height:18px"></i></button></div>
            <div class="modal-body">
                <div class="field"><label>Title</label><input id="prTitle" placeholder="What do you need prayer for?"></div>
                <div class="field"><label>Description</label><textarea id="prDesc" placeholder="Share as much as you'd like..."></textarea></div>
                <div class="grid-2">
                    <div class="field"><label>Category</label>
                        <select id="prCat">
                            <option value="general">General</option>
                            <option value="health">Health</option>
                            <option value="family">Family</option>
                            <option value="financial">Financial</option>
                            <option value="spiritual">Spiritual</option>
                        </select></div>
                    <div class="field" style="display:flex;flex-direction:column;gap:8px;padding-top:22px">
                        <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
                            <input type="checkbox" id="prAnon"> Post Anonymously
                        </label>
                        <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
                            <input type="checkbox" id="prUrgent"> Mark as Urgent
                        </label>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="addPrayer()">Submit Prayer</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);
    refreshIcons();
}

async function addPrayer() {
    try {
        await apiPost('/prayers', {
            title: document.getElementById('prTitle').value,
            description: document.getElementById('prDesc').value,
            category: document.getElementById('prCat').value,
            is_anonymous: document.getElementById('prAnon').checked,
            is_urgent: document.getElementById('prUrgent').checked
        });
        document.querySelector('.modal-overlay')?.remove();
        renderPrayers();
    } catch (e) { alert(e.message); }
}

// ── FEED ──────────────────
async function renderFeed() {
    const area = document.getElementById('contentArea');
    try {
        const posts = await apiGet('/feed');
        area.innerHTML = `
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">${icon('newspaper', 16)} Church Feed</div>
                    <div class="panel-actions">
                        <button class="btn btn-primary" onclick="showAddPostModal()">+ New Post</button>
                    </div>
                </div>
                ${posts.length === 0
                    ? `<div class="empty-state"><div class="empty-state-icon">${icon('newspaper', 40)}</div>
                        <div class="empty-state-title">No posts yet</div>
                        <div class="empty-state-text">Share an update with your church</div></div>`
                    : posts.map(p => `
                        <div class="list-item">
                            <div class="list-item-icon" style="background:rgba(108,92,231,0.15)">
                                ${p.is_pinned ? icon('pin', 20) : icon('file-text', 20)}
                            </div>
                            <div class="list-item-content">
                                <div class="list-item-title">${p.author_name || 'Church'}</div>
                                <div class="list-item-sub" style="margin-top:4px;line-height:1.5">${p.content}</div>
                                <div class="list-item-meta">
                                    ${icon('heart', 12)} ${p.like_count || 0} &nbsp;&middot;&nbsp;
                                    ${icon('message-circle', 12)} ${p.comment_count || 0} &nbsp;&middot;&nbsp;
                                    ${timeAgo(p.created_at)}
                                    ${p.is_pinned ? ' &middot; <span class="badge badge-gold">Pinned</span>' : ''}
                                </div>
                            </div>
                        </div>
                    `).join('')
                }
            </div>
        `;
        refreshIcons();
    } catch (e) {
        area.innerHTML = `<div class="empty-state"><div class="empty-state-icon">${icon('alert-circle', 40)}</div>
            <div class="empty-state-title">${e.message}</div></div>`;
        refreshIcons();
    }
}

function showAddPostModal() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-header"><h3>New Post</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()"><i data-lucide="x" style="width:18px;height:18px"></i></button></div>
            <div class="modal-body">
                <div class="field"><label>Content</label>
                    <textarea id="postContent" placeholder="Share an update with your church..." style="min-height:120px"></textarea></div>
                <div class="field"><label>Visibility</label>
                    <select id="postVis">
                        <option value="all_members">All Members</option>
                        <option value="leaders_only">Leaders Only</option>
                    </select></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="addPost()">Publish</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);
    refreshIcons();
}

async function addPost() {
    try {
        await apiPost('/feed', {
            content: document.getElementById('postContent').value,
            visibility: document.getElementById('postVis').value
        });
        document.querySelector('.modal-overlay')?.remove();
        renderFeed();
    } catch (e) { alert(e.message); }
}

// ── SHORTS ──────────────────
async function renderShorts() {
    const area = document.getElementById('contentArea');
    try {
        const [shorts, trending] = await Promise.all([
            apiGet('/shorts/my-church'),
            apiGet('/shorts/trending')
        ]);
        area.innerHTML = `
            <div class="stats-grid" style="grid-template-columns:repeat(auto-fill,minmax(180px,1fr))">
                <div class="stat-card purple">
                    <div class="stat-icon">${icon('clapperboard', 22)}</div>
                    <div class="stat-value">${shorts.length}</div>
                    <div class="stat-label">Your Church Shorts</div>
                </div>
                <div class="stat-card teal">
                    <div class="stat-icon">${icon('flame', 22)}</div>
                    <div class="stat-value">${trending.length}</div>
                    <div class="stat-label">Trending Now</div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">${icon('flame', 16)} Trending Shorts (All Churches)</div>
                </div>
                ${trending.length === 0
                    ? `<div class="empty-state"><div class="empty-state-icon">${icon('clapperboard', 40)}</div>
                        <div class="empty-state-title">No shorts yet</div></div>`
                    : trending.map(s => `
                        <div class="list-item">
                            <div class="list-item-icon" style="background:rgba(253,121,168,0.15)">${icon('play-circle', 20)}</div>
                            <div class="list-item-content">
                                <div class="list-item-title">${s.title}</div>
                                <div class="list-item-sub">${s.description || ''}</div>
                                <div class="list-item-meta">
                                    ${s.church_name || ''} &nbsp;&middot;&nbsp;
                                    ${icon('eye', 12)} ${s.view_count || 0} views &nbsp;&middot;&nbsp;
                                    ${icon('heart', 12)} ${s.like_count || 0} &nbsp;&middot;&nbsp;
                                    ${icon('message-circle', 12)} ${s.comment_count || 0} &nbsp;&middot;&nbsp;
                                    <span class="badge badge-purple">${s.category || 'general'}</span>
                                </div>
                            </div>
                        </div>
                    `).join('')
                }
            </div>
        `;
        refreshIcons();
    } catch (e) {
        area.innerHTML = `<div class="empty-state"><div class="empty-state-icon">${icon('alert-circle', 40)}</div>
            <div class="empty-state-title">${e.message}</div></div>`;
        refreshIcons();
    }
}

// ── GIVING ──────────────────
async function renderGiving() {
    const area = document.getElementById('contentArea');
    try {
        const [trends, givingAnalytics, funds] = await Promise.all([
            apiGet('/reports/analytics/giving-trends'),
            apiGet('/reports/giving'),
            apiGet('/funds')
        ]);
        const months = trends.monthly_trends || [];
        const totalThisYear = months.reduce((s, m) => s + m.current_year, 0);
        const totalLastYear = months.reduce((s, m) => s + m.previous_year, 0);
        const maxMonth = Math.max(...months.map(m => m.current_year), 1);

        const byFund = givingAnalytics.by_fund || [];
        // Color palette for charts
        const colors = ['#fd79a8', '#00cec9', '#f0c040', '#6c5ce7', '#ff6b6b', '#51cf66', '#a29bfe', '#fdcb6e'];

        area.innerHTML = `
            <div class="stats-grid" style="grid-template-columns:repeat(auto-fill,minmax(200px,1fr))">
                <div class="stat-card gold">
                    <div class="stat-icon">${icon('wallet', 22)}</div>
                    <div class="stat-value">$${parseFloat(totalThisYear).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                    <div class="stat-label">Year to Date (${trends.year})</div>
                </div>
                <div class="stat-card teal">
                    <div class="stat-icon">${icon('bar-chart-3', 22)}</div>
                    <div class="stat-value">$${parseFloat(totalLastYear).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                    <div class="stat-label">Previous Year</div>
                </div>
                <div class="stat-card ${totalThisYear >= totalLastYear ? 'purple' : 'pink'}">
                    <div class="stat-icon">${totalThisYear >= totalLastYear ? icon('trending-up', 22) : icon('trending-down', 22)}</div>
                    <div class="stat-value">${totalLastYear ? Math.round((totalThisYear - totalLastYear) / totalLastYear * 100) : 0}%</div>
                    <div class="stat-label">Year over Year</div>
                </div>
            </div>

            <div class="grid-2" style="margin-bottom:20px">
                <div class="panel" style="margin-bottom:0">
                    <div class="panel-header">
                        <div class="panel-title">${icon('wallet', 16)} Monthly Giving (${trends.year})</div>
                    </div>
                    <div class="panel-body">
                        ${months.length === 0 ? '<div class="empty-state">No monthly data</div>' : months.map(m => `
                            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
                                <div style="width:50px;font-size:12px;color:var(--text-muted);text-align:right">${m.month.slice(0,3)}</div>
                                <div style="flex:1;height:24px;background:var(--border);border-radius:4px;overflow:hidden;position:relative">
                                    <div style="height:100%;width:${(m.current_year/maxMonth)*100}%;background:linear-gradient(90deg,var(--accent),var(--accent-light));border-radius:4px;transition:width 0.5s"></div>
                                </div>
                                <div style="width:80px;font-size:12px;font-weight:600;text-align:right">$${parseFloat(m.current_year).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                                <div style="width:60px;font-size:11px;text-align:right;color:${m.yoy_change_pct > 0 ? 'var(--success)' : m.yoy_change_pct < 0 ? 'var(--danger)' : 'var(--text-muted)'}">
                                    ${m.yoy_change_pct !== null ? (m.yoy_change_pct > 0 ? '+' : '') + m.yoy_change_pct + '%' : '—'}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="panel" style="margin-bottom:0">
                    <div class="panel-header">
                        <div class="panel-title">${icon('pie-chart', 16)} Fund Distribution</div>
                    </div>
                    <div class="panel-body" style="display:flex;justify-content:center;align-items:center;height:250px">
                        ${byFund.length === 0 
                            ? `<div class="empty-state-title">No donations recorded yet</div>`
                            : `<canvas id="fundPieChart"></canvas>`}
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">${icon('layers', 16)} Fund Management</div>
                    <div class="panel-actions">
                        <button class="btn btn-primary" onclick="showAddFundModal()">+ Create Fund</button>
                    </div>
                </div>
                <div class="panel-body">
                    ${funds.length === 0
                        ? `<div class="empty-state">
                            <div class="empty-state-title">No Funds Created</div>
                            <div class="empty-state-text">Create funds like Tithes, Offering, or Building Fund.</div>
                           </div>`
                        : `<table class="data-table">
                            <thead><tr><th>Fund Name</th><th>Type</th><th>Current Balance</th><th>Status</th></tr></thead>
                            <tbody>
                                ${funds.map(f => `
                                    <tr>
                                        <td><strong>${f.name}</strong><br><span style="font-size:11px;color:var(--text-muted)">${f.description || ''}</span></td>
                                        <td><span class="badge badge-purple">${f.fund_type}</span> ${f.is_restricted ? '<span class="badge badge-danger">Restricted</span>' : ''}</td>
                                        <td><strong>$${parseFloat(f.current_balance || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</strong></td>
                                        <td>${f.is_active ? '<span style="color:var(--success)">Active</span>' : '<span style="color:var(--text-muted)">Inactive</span>'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                           </table>`
                    }
                </div>
            </div>
        `;
        refreshIcons();

        // Draw Pie Chart
        if (byFund.length > 0) {
            const ctx = document.getElementById('fundPieChart')?.getContext('2d');
            if (ctx) {
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: byFund.map(f => f.fund_name),
                        datasets: [{
                            data: byFund.map(f => parseFloat(f.total)),
                            backgroundColor: colors.slice(0, byFund.length),
                            borderWidth: 0,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: { color: '#f0f0f8', font: { family: 'Inter', size: 12 } }
                            }
                        }
                    }
                });
            }
        }

    } catch (e) {
        area.innerHTML = `<div class="empty-state"><div class="empty-state-icon">${icon('alert-circle', 40)}</div>
            <div class="empty-state-title">${e.message}</div></div>`;
        refreshIcons();
    }
}

function showAddFundModal() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-header"><h3>Create New Fund</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()"><i data-lucide="x" style="width:18px;height:18px"></i></button></div>
            <div class="modal-body">
                <div class="field"><label>Fund Name</label><input id="fdName" placeholder="e.g. Building Fund"></div>
                <div class="field"><label>Description</label><input id="fdDesc" placeholder="Optional details..."></div>
                <div class="field"><label>Fund Type</label>
                    <select id="fdType">
                        <option value="general">General</option>
                        <option value="missions">Missions</option>
                        <option value="building">Building</option>
                        <option value="benevolence">Benevolence</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                <label style="display:flex;align-items:center;gap:8px;font-size:13px;margin-top:20px;cursor:pointer">
                    <input type="checkbox" id="fdRestrict"> This is a restricted fund
                </label>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="addFund()">Create Fund</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);
    refreshIcons();
}

async function addFund() {
    try {
        await apiPost('/funds', {
            name: document.getElementById('fdName').value,
            description: document.getElementById('fdDesc').value || null,
            fund_type: document.getElementById('fdType').value,
            is_restricted: document.getElementById('fdRestrict').checked,
            is_active: true
        });
        document.querySelector('.modal-overlay')?.remove();
        renderGiving();
    } catch (e) { alert(e.message); }
}

// ── NOTIFICATIONS ──────────────────
async function renderNotifications() {
    const area = document.getElementById('contentArea');
    try {
        const data = await apiGet('/notifications');
        const items = data.items || [];
        area.innerHTML = `
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">${icon('bell', 16)} Notifications (${data.unread_count || 0} unread)</div>
                    <div class="panel-actions">
                        ${data.unread_count > 0
                            ? `<button class="btn btn-sm btn-secondary" onclick="markAllRead()">Mark All Read</button>`
                            : ''}
                    </div>
                </div>
                ${items.length === 0
                    ? `<div class="empty-state"><div class="empty-state-icon">${icon('bell-off', 40)}</div>
                        <div class="empty-state-title">All clear!</div>
                        <div class="empty-state-text">No notifications right now</div></div>`
                    : items.map(n => `
                        <div class="list-item" style="${!n.is_read ? 'background:rgba(108,92,231,0.05)' : ''}">
                            <div class="list-item-icon" style="background:${!n.is_read ? 'rgba(108,92,231,0.2)' : 'rgba(255,255,255,0.04)'}">
                                ${getNotifIcon(n.type)}
                            </div>
                            <div class="list-item-content">
                                <div class="list-item-title" style="${n.is_read ? 'color:var(--text-secondary);font-weight:400' : ''}">${n.title}</div>
                                <div class="list-item-sub">${n.body || ''}</div>
                                <div class="list-item-meta">${timeAgo(n.created_at)}</div>
                            </div>
                            ${!n.is_read ? `<button class="btn btn-sm btn-secondary" onclick="markRead('${n.id}')"><i data-lucide="check" style="width:14px;height:14px"></i></button>` : ''}
                        </div>
                    `).join('')
                }
            </div>
        `;
        refreshIcons();
    } catch (e) {
        area.innerHTML = `<div class="empty-state"><div class="empty-state-icon">${icon('alert-circle', 40)}</div>
            <div class="empty-state-title">${e.message}</div></div>`;
        refreshIcons();
    }
}

function getNotifIcon(type) {
    const icons = {
        like: icon('heart', 18),
        comment: icon('message-circle', 18),
        rsvp: icon('calendar-check', 18),
        prayer: icon('hand-heart', 18),
        event: icon('calendar-days', 18),
        short: icon('clapperboard', 18)
    };
    return icons[type] || icon('bell', 18);
}

async function markRead(id) {
    try { await apiPost(`/notifications/${id}/read`); renderNotifications(); loadNotificationCount(); } catch (e) { alert(e.message); }
}

async function markAllRead() {
    try { await apiPost('/notifications/read-all'); renderNotifications(); loadNotificationCount(); } catch (e) { alert(e.message); }
}

async function loadNotificationCount() {
    try {
        const data = await apiGet('/notifications');
        const count = data.unread_count || 0;
        const badge = document.getElementById('notifBadge');
        const dot = document.getElementById('notifDot');
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = '';
            dot.style.display = '';
        } else {
            badge.style.display = 'none';
            dot.style.display = 'none';
        }
    } catch (e) { /* silent fail */ }
}

// Refresh notification count every 30s
setInterval(loadNotificationCount, 30000);
