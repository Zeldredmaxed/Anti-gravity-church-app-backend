import React, { useEffect, useState } from 'react';
import { dashboardService, type DashboardMetrics, type DashboardActivity } from '../api/services/dashboard.service';
import './DashboardView.css';

export function DashboardView() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [activities, setActivities] = useState<DashboardActivity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [metricsData, activityData] = await Promise.all([
          dashboardService.getMetrics(),
          dashboardService.getActivityFeed()
        ]);
        setMetrics(metricsData);
        setActivities(activityData);
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  return (
    <>
      <section className="hero">
        <h1>Welcome back, Pastor David</h1>
        <h2 className="text-muted">Church Dashboard (Command Center)</h2>
        
        <div className="quick-actions">
          <button className="btn btn-yellow"><i className="fa-solid fa-user-plus"></i> Add Member</button>
          <button className="btn btn-gray"><i className="fa-solid fa-user-check"></i> Log Attendance</button>
          <button className="btn btn-white"><i className="fa-regular fa-envelope"></i> Send Message</button>
        </div>
      </section>

      <main className="dashboard-grid">
        
        <div className="flex-col gap-20">
          <div className="glass-card">
            <div className="progress-section">
              <div className="progress-header"><span>Groups</span><span>{metrics?.groups.total ?? 0}</span></div>
              <div className="progress-track"><div className="progress-fill fill-yellow" style={{width: '25%'}}></div></div>
              <div style={{fontSize: 10, marginTop: 3}}>+{metrics?.groups.trend ?? 0} this month</div>
            </div>
            <div className="progress-section">
              <div className="progress-header"><span>Members</span><span>{metrics?.members.total ?? 0}</span></div>
              <div className="progress-track"><div className="progress-fill fill-dark" style={{width: '78%'}}></div></div>
              <div style={{fontSize: 10, marginTop: 3}}>+{metrics?.members.trend ?? 0}% growth</div>
            </div>
            <div className="progress-section">
              <div className="progress-header"><span>Attendance</span><span>{metrics?.attendance.total ?? 0}</span></div>
              <div className="progress-track"><div className="progress-fill fill-striped" style={{width: '65%'}}></div></div>
            </div>
          </div>

          <div className="glass-card ai-insights">
            <h3>AI Insights <img src="https://i.pravatar.cc/150?img=5" style={{width: 24, height: 24, borderRadius: '50%', float: 'right'}} alt="AI avatar" /></h3>
            <ul>
              <li>3 long-term visitors are ready for next steps.</li>
              <li>Upcoming event: Youth Camp - planning complete.</li>
              <li>Prayer request trend: 5 new requests this week.</li>
            </ul>
            <div className="insight-buttons">
              <button className="btn-dark">"View Members" <span>opens filtered Members page</span></button>
              <button className="btn-dark">"Send Follow-Up" <span>opens communication modal</span></button>
            </div>
          </div>
        </div>

        <div className="flex-col gap-20">
          <div className="glass-card">
            <h3>Goal Output</h3>
            <div className="donut-wrapper">
              <div className="donut-chart">
                <div className="donut-inner">10%</div>
              </div>
            </div>
          </div>
          <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <div className="avatar-list">
              <div className="avatar-row">
                <img src="https://i.pravatar.cc/150?img=1" className="avatar-small" alt="a" />
                <img src="https://i.pravatar.cc/150?img=2" className="avatar-small" alt="b" />
              </div>
              <div style={{ width: '80%', height: 1, background: 'rgba(0,0,0,0.1)', margin: '5px 0' }}></div>
              <div style={{ width: '80%', height: 1, background: 'rgba(0,0,0,0.1)', margin: '5px 0' }}></div>
              <div style={{ width: '80%', height: 1, background: 'rgba(0,0,0,0.1)', margin: '5px 0' }}></div>
              <div className="avatar-row" style={{ marginTop: 10 }}>
                <img src="https://i.pravatar.cc/150?img=3" className="avatar-small" alt="c" />
                <img src="https://i.pravatar.cc/150?img=4" className="avatar-small" alt="d" />
                <div className="avatar-small avatar-yellow"></div>
              </div>
              <div className="letters"><span>S</span><span>W</span><span>T</span></div>
            </div>
          </div>
        </div>

        <div className="flex-col gap-20">
          <div className="top-stats-container">
            <div className="glass-card stat-card">
              <h3>Total Members</h3>
              <div className="large-stat">{loading ? '...' : (metrics?.members.total.toLocaleString() ?? '0')}</div>
              <i className="fa-solid fa-users stat-icon-bottom"></i>
            </div>
            <div className="glass-card stat-card">
              <h3>Weekly Attendance</h3>
              <div className="large-stat">{loading ? '...' : (metrics?.attendance.total.toLocaleString() ?? '0')}</div>
              <i className="fa-solid fa-users stat-icon-bottom"></i>
              {metrics && metrics.attendance.trend > 0 && <div className="stat-trend"><i className="fa-solid fa-arrow-up"></i></div>}
            </div>
          </div>

          <div className="glass-card" style={{ flex: 1 }}>
            <div className="calendar-header">
              <h3>Calendar - Next 7 Days</h3>
              <button className="btn-add-event">+ Add Event</button>
            </div>
            
            <div className="calendar-grid">
              <div className="time-col">
                <span>8:00 AM</span>
                <span>9:00 AM</span>
                <span>12:00 PM</span>
                <span>12:30 PM</span>
              </div>
              <div className="days-col">
                <div className="days-header">
                  <div className="day">Mon<br/>22</div>
                  <div className="day">Tue<br/>23</div>
                  <div className="day">Wed<br/>24</div>
                  <div className="day">Thu<br/>25</div>
                  <div className="day">Fri<br/>26</div>
                  <div className="day">Sat<br/>27</div>
                  <div className="day">Sun<br/>28</div>
                </div>
                <div className="calendar-body">
                  <div className="event event-white"><i className="fa-regular fa-clipboard"></i> Morning Service Prep</div>
                  <div className="event event-dark"><i className="fa-solid fa-cross"></i> Sunday Service</div>
                  <div className="event event-light"><i className="fa-solid fa-mug-hot"></i> Youth Group <img src="https://i.pravatar.cc/150?img=8" style={{width: 16, height: 16, borderRadius: '50%', marginLeft: 5}} alt="avatar" /></div>
                  <div className="event event-outline"><i className="fa-solid fa-book-open"></i> Mid-week Study</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex-col gap-20">
          <div className="glass-card sidebar-stat">
            <h3>Monthly Giving</h3>
            <div className="large-stat">${loading ? '...' : (metrics?.giving.total.toLocaleString() ?? '0')}</div>
            <div className="stat-trend">
              <i className="fa-solid fa-sack-dollar" style={{color: '#333', fontSize: 24}}></i> 
              {metrics && metrics.giving.trend > 0 && <i className="fa-solid fa-arrow-up" style={{position: 'absolute', top: 0, right: -15}}></i>}
            </div>
          </div>
          
          <div className="glass-card sidebar-stat">
            <h3>Recent Activity</h3>
            {activities.length > 0 ? (
              <div style={{ marginTop: '15px' }}>
                {activities.slice(0, 2).map((activity) => (
                  <div key={activity.id} style={{ marginBottom: '10px', fontSize: '0.9rem' }}>
                    <strong>{activity.action}</strong>
                    <div style={{ color: '#666', fontSize: '0.8rem' }}>{activity.time}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="large-stat">0</div>
            )}
          </div>

          <div className="glass-card action-center">
            <h3>Action Center</h3>
            <div className="action-list">
              <div className="action-item">
                <div className="action-icon"><i className="fa-solid fa-hands-praying"></i></div>
                <div className="action-text">
                  <div className="action-title">Prayer Request</div>
                  <div className="action-time">Sep 13, 08:30</div>
                </div>
                <i className="fa-solid fa-circle-check check-icon"></i>
              </div>
              <div className="action-item">
                <div className="action-icon"><i className="fa-regular fa-user"></i></div>
                <div className="action-text">
                  <div className="action-title">Missed Attendance</div>
                  <div className="action-time">Sep 13, 10:30</div>
                </div>
                <i className="fa-solid fa-circle-check check-icon"></i>
              </div>
              <div className="action-item">
                <div className="action-icon"><i className="fa-solid fa-droplet"></i></div>
                <div className="action-text">
                  <div className="action-title">Baptism Candidates</div>
                  <div className="action-time">Sep 13, 13:00</div>
                </div>
                <i className="fa-solid fa-circle-check check-icon"></i>
              </div>
            </div>
          </div>
        </div>

      </main>
    </>
  );
}
