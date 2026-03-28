import React, { useState } from 'react';
import { 
  MessageSquare, Pencil, GraduationCap, Plus, 
  Trash2, ChevronDown
} from 'lucide-react';
import './ProfileView.css';

export function ProfileView() {
  const [toggles, setToggles] = useState([true, false, false]);

  const toggleSwitch = (index: number) => {
    const newToggles = [...toggles];
    newToggles[index] = !newToggles[index];
    setToggles(newToggles);
  };

  return (
    <div className="profile-view">
      
      <div className="top-row">
        
        {/* Left Column: Profile Card */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="profile-img-container">
            <img src="https://i.pravatar.cc/300?img=11" alt="John Doe" />
            <div className="profile-overlay">
              <h2>John Doe</h2>
              <p>Member Since Jan 2018</p>
            </div>
          </div>
          <div className="giving-pill">
            <strong>$12,000</strong> YTD Giving
          </div>
        </div>

        {/* Middle Column: Tracker */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="action-buttons">
            <button className="btn-outline">
              <MessageSquare size={16} /> Message Member
            </button>
            <button className="btn-glass">
              <Pencil size={16} /> Edit Profile
            </button>
          </div>
          
          <div className="widget" style={{ flex: 1, position: 'relative' }}>
            <h3 className="widget-title">Spiritual Journey Tracker</h3>
            <Pencil size={16} style={{ position: 'absolute', top: 24, right: 24, color: 'var(--text-muted)', cursor: 'pointer' }} />
            
            <div className="tracker-layout">
              <div className="toggles-list">
                
                <div className="toggle-item">
                  <div 
                    className={`toggle-switch ${toggles[0] ? 'active' : ''}`}
                    onClick={() => toggleSwitch(0)}
                  >
                    <div className="toggle-knob"></div>
                  </div>
                  <div className="toggle-text">
                    <h4>Mark Saved</h4>
                    <p>Saved Date: Jun 15, 2018</p>
                  </div>
                </div>

                <div className="toggle-item">
                  <div 
                    className={`toggle-switch ${toggles[1] ? 'active' : ''}`}
                    onClick={() => toggleSwitch(1)}
                  >
                    <div className="toggle-knob"></div>
                  </div>
                  <div className="toggle-text">
                    <h4>Mark Baptized</h4>
                    <p>Baptized: Not Set / [Select Date]</p>
                  </div>
                </div>

                <div className="toggle-item">
                  <div 
                    className={`toggle-switch ${toggles[2] ? 'active' : ''}`}
                    onClick={() => toggleSwitch(2)}
                  >
                    <div className="toggle-knob"></div>
                  </div>
                  <div className="toggle-text">
                    <h4>Mark Completed Class</h4>
                    <p>Class: Not Started / [Search Classes]</p>
                  </div>
                </div>

              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div className="donut-container">
                  <svg width="120" height="120" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(0,0,0,0.15)" strokeWidth="8" strokeDasharray="4 6" transform="rotate(-90 60 60)" />
                    <circle cx="60" cy="60" r="50" fill="none" stroke="#fcd56e" strokeWidth="8" strokeDasharray="110 314" strokeLinecap="round" transform="rotate(-90 60 60)" />
                  </svg>
                  <div className="donut-text">
                    <h3>35%</h3>
                    <p>Overall Spiritual Growth Progress</p>
                  </div>
                </div>
                <GraduationCap className="grad-icon" size={24} />
              </div>

            </div>
          </div>
        </div>

        {/* Right Column: Notes */}
        <div className="widget">
          <h3 className="widget-title">Member Notes</h3>
          <button className="btn-yellow">
            <Plus size={16} /> Add New Note
          </button>
          
          <div className="notes-list">
            <div className="note-item">
              <div>
                <div className="note-meta">Sep 10, 2024 | Lora P. from Crextio</div>
                <div className="note-text">Discussed class registration</div>
              </div>
              <div className="note-actions">
                <button className="note-btn"><Pencil size={12} /></button>
                <button className="note-btn"><Trash2 size={12} /></button>
              </div>
            </div>
            <div className="note-item">
              <div>
                <div className="note-meta">Sep 10, 2024 | Lora P. from Crextio</div>
                <div className="note-text">Discussed class registration</div>
              </div>
              <div className="note-actions">
                <button className="note-btn"><Pencil size={12} /></button>
                <button className="note-btn"><Trash2 size={12} /></button>
              </div>
            </div>
            <div className="note-item">
              <div>
                <div className="note-meta">Sep 10, 2024 | Lora P. from Crextio</div>
                <div className="note-text">Discussed class propronuration</div>
              </div>
              <div className="note-actions">
                <button className="note-btn"><Pencil size={12} /></button>
                <button className="note-btn"><Trash2 size={12} /></button>
              </div>
            </div>
          </div>
        </div>

      </div>

      <div className="bottom-row">
        
        {/* Left Bottom: Giving Summary */}
        <div className="widget">
          <div className="summary-header">
            <h3 className="widget-title" style={{ margin: 0 }}>Giving Summary</h3>
            <div style={{ display: 'flex', gap: '10px' }}>
              <div className="dropdown-pill">Month: Sep 2024 <ChevronDown size={12} /></div>
              <div className="dropdown-pill">Year: 2024 <ChevronDown size={12} /></div>
            </div>
          </div>
          
          <div className="stat-row">
            <div>Total Given (YTD): <strong>$12,000</strong></div>
            <div>Average Monthly: <strong>$1,000</strong></div>
            <div>Last Giving: <strong>$500</strong> <span style={{ color: 'var(--text-muted)' }}>(Sep 1st)</span></div>
          </div>

          <div className="area-chart">
            <svg viewBox="0 0 500 100" preserveAspectRatio="none" style={{ width: '100%', height: '100%', overflow: 'visible' }}>
              <defs>
                <linearGradient id="yellowGlow" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="rgba(252, 213, 110, 0.6)" />
                  <stop offset="100%" stopColor="rgba(252, 213, 110, 0)" />
                </linearGradient>
              </defs>
              <path d="M0,80 C30,60 60,90 100,60 C140,30 160,100 200,80 C230,60 260,30 300,50 C340,70 360,90 400,60 C440,30 460,90 500,40 L500,100 L0,100 Z" fill="url(#yellowGlow)" />
              <path d="M0,80 C30,60 60,90 100,60 C140,30 160,100 200,80 C230,60 260,30 300,50 C340,70 360,90 400,60 C440,30 460,90 500,40" fill="none" stroke="#fcd56e" strokeWidth="4" strokeLinecap="round" />
            </svg>
          </div>
        </div>

        {/* Right Bottom: Attendance Summary */}
        <div className="widget" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div className="summary-header">
            <h3 className="widget-title" style={{ margin: 0 }}>Attendance Summary</h3>
            <div style={{ fontSize: '13px' }}>Avg. Attendance Rate (YTD): <strong>88%</strong></div>
          </div>
          
          <div>
            <div className="bar-chart-container">
              <div className="bar" style={{ height: '60%' }}></div>
              <div className="bar" style={{ height: '50%' }}></div>
              <div className="bar" style={{ height: '75%' }}></div>
              <div className="bar" style={{ height: '85%' }}></div>
              <div className="bar" style={{ height: '45%' }}></div>
              <div className="bar" style={{ height: '80%' }}></div>
              <div className="bar" style={{ height: '65%' }}></div>
              <div className="bar" style={{ height: '65%' }}></div>
              <div className="bar" style={{ height: '55%' }}></div>
            </div>
            <div className="chart-footer">[Click data points to drill down to event details]</div>
          </div>
        </div>

      </div>
    </div>
  );
}
