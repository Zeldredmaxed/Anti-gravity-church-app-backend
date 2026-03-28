import React, { useState, useEffect } from 'react';
import { 
  Search, Filter, ChevronDown, Calendar, ChevronRight, 
  Menu, Users, UsersRound, CalendarDays 
} from 'lucide-react';
import './VolunteersView.css';

import { volunteersService } from '../api/services/volunteers.service';
import type { Volunteer } from '../api/services/volunteers.service';
const availableVolunteers = [
  { id: 'val1', name: 'John Doe', avatar: 'https://i.pravatar.cc/150?img=11', opacity: 1 },
  { id: 'val2', name: 'Jane Doe', avatar: 'https://i.pravatar.cc/150?img=9', opacity: 1 },
  { id: 'val3', name: 'Lora Piterson', avatar: 'https://i.pravatar.cc/150?img=5', opacity: 0.3 },
  { id: 'val4', name: 'John Doe', avatar: 'https://i.pravatar.cc/150?img=12', opacity: 1 },
  { id: 'val5', name: 'Jane Doe', avatar: 'https://i.pravatar.cc/150?img=1', opacity: 1 },
];

const mockRoles = [
  'Welcome Team',
  'Audio/Visual',
  'Sunday School Teacher',
  'Usher',
  'Worship Team'
];

export function VolunteersView() {
  const [dropdownOpenId, setDropdownOpenId] = useState<string | null>(null);
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchVolunteers();
  }, []);

  const fetchVolunteers = async () => {
    try {
      setIsLoading(true);
      const data = await volunteersService.getVolunteerList();
      setVolunteers(data);
    } catch (error) {
      console.error('Failed to fetch volunteers:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleDropdown = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDropdownOpenId(dropdownOpenId === id ? null : id);
  };

  // Close dropdowns if clicked outside
  React.useEffect(() => {
    const handleOutsideClick = () => setDropdownOpenId(null);
    window.addEventListener('click', handleOutsideClick);
    return () => window.removeEventListener('click', handleOutsideClick);
  }, []);

  return (
    <div className="volunteers-view">
      <div className="page-header">
        <div className="title-section">
          <h1>VOLUNTEERS</h1>
          <p>Welcome to Church Management System (ChMS)</p>
        </div>
        <div className="action-section">
          <div className="search-bar">
            <Search size={16} />
            <input type="text" placeholder="Search" />
          </div>
          <button className="btn btn-outline" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Filter size={16} /> Filter
          </button>
          <button className="btn btn-gold">Add Volunteer</button>
        </div>
      </div>

      <div className="dashboard-grid">
        
        {/* Left Panel: Volunteer Management */}
        <div className="glass-panel volunteer-mgmt">
          <div className="panel-header">VOLUNTEER MANAGEMENT</div>
          
          <div className="volunteer-table-wrapper">
            <table className="volunteer-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Availability</th>
                  <th>Team</th>
                  <th>Contact</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '2rem' }}>Loading volunteers...</td>
                  </tr>
                ) : volunteers.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No volunteers found.</td>
                  </tr>
                ) : volunteers.map(vol => (
                  <tr key={vol.id}>
                    <td>
                      <div className="user-cell">
                        <img src={vol.avatar} alt={vol.name} /> {vol.name}
                      </div>
                    </td>
                    <td style={{ position: 'relative' }}>
                      <div 
                        className="role-dropdown-btn" 
                        onClick={(e) => toggleDropdown(vol.id, e)}
                      >
                        {vol.role || 'Assign Role'} <ChevronDown size={12} />
                      </div>
                      {dropdownOpenId === vol.id && (
                        <div className="role-menu" onClick={(e) => e.stopPropagation()}>
                          {mockRoles.map(role => (
                            <div 
                              key={role} 
                              className={`role-menu-item ${role === vol.role ? 'highlight' : ''}`}
                            >
                              {role}
                            </div>
                          ))}
                        </div>
                      )}
                    </td>
                    <td>
                      <label className="toggle-switch">
                        <input type="checkbox" defaultChecked={vol.available} />
                        <span className="slider"></span>
                      </label>
                    </td>
                    <td>{vol.team}</td>
                    <td>{vol.contact}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Panel: Schedule & Planning */}
        <div className="glass-panel schedule-planning">
          <div className="sp-header">
            <div className="panel-header" style={{ marginBottom: 0 }}>SCHEDULE & PLANNING</div>
            <div className="sp-actions">
              <button className="btn btn-gold">Save Schedule</button>
              <button className="btn btn-dark">Edit Schedule</button>
              <button className="btn btn-outline">Notify Volunteers</button>
            </div>
          </div>

          <div className="schedule-sub">
            <div className="date-range">Oct 1-7, 2024</div>
            <div className="today-btn">
              <Calendar size={14} /> Today <ChevronRight size={12} />
            </div>
          </div>

          <div className="schedule-layout">
            <div className="avail-volunteers">
              <div className="avail-title">AVAILABLE VOLUNTEERS</div>
              <div className="avail-list">
                {availableVolunteers.map(vol => (
                  <div key={vol.id} className="avail-item" style={{ opacity: vol.opacity }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <img src={vol.avatar} alt={vol.name} /> {vol.name}
                    </div>
                    <Menu size={14} />
                  </div>
                ))}
              </div>
            </div>

            <div className="cal-grid">
              <div className="cal-header">Sun<br />9:00 AM</div>
              <div className="cal-header">Sun<br />11:00 AM</div>
              <div className="cal-header">Mon<br />11:00 AM</div>
              <div className="cal-header">Wed<br />2:00 AM</div>
              <div className="cal-header">Thu<br />5:00 AM</div>
              <div className="cal-header">Fri<br />7:00 AM</div>

              <div className="cal-cell"><div className="slot">Sun<br/>9:00 AM</div></div>
              <div className="cal-cell"></div>
              <div className="cal-cell"></div>
              <div className="cal-cell"><div className="slot">Mid-week<br/>7:00 AM</div></div>
              <div className="cal-cell"></div>
              <div className="cal-cell"></div>

              <div className="cal-cell">
                <div className="drop-zone"></div>
              </div>
              <div className="cal-cell"></div>
              <div className="cal-cell"></div>
              <div className="cal-cell"><div className="slot">Mid-week<br/>7:00 PM</div></div>
              <div className="cal-cell"></div>
              <div className="cal-cell"></div>

              <div className="cal-cell"></div>
              <div className="cal-cell"><div className="slot">Sun<br/>11:00 AM</div></div>
              <div className="cal-cell"></div>
              <div className="cal-cell"></div>
              <div className="cal-cell"><div className="slot">Mid-week<br/>7:00 PM</div></div>
              <div className="cal-cell"><div className="slot">Mid-week<br/>6:00 PM</div></div>

              <div className="cal-cell"><div className="slot">Mid-week<br/>7:00 PM</div></div>
              <div className="cal-cell"></div>
              <div className="cal-cell"><div className="slot">Mid-week<br/>7:00 PM</div></div>
              <div className="cal-cell"><div className="slot">Mid-week<br/>7:00 PM</div></div>
              <div className="cal-cell"></div>
              <div className="cal-cell"></div>
            </div>
          </div>
        </div>

      </div>

      <div className="bottom-stats">
        <div className="stat-item">
          <Users size={16} /> Total Volunteers: 203
        </div>
        <div className="stat-item">
          <UsersRound size={16} /> Active Teams: 12
        </div>
        <div className="stat-item">
          <CalendarDays size={16} /> Service Times: 3
        </div>
      </div>

    </div>
  );
}
