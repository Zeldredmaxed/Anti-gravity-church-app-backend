import React, { useState } from 'react';
import { 
  Pencil, Upload, User, Settings as SettingsIcon, RefreshCw,
  Users, UserPlus, Clock, Key, Heart, Trash2, Plus, X, Check
} from 'lucide-react';
import { adminService } from '../api/services/admin.service';
import type { ChurchSettings } from '../api/services/admin.service';
import './SettingsView.css';

interface Role {
  id: string;
  name: string;
  icon: React.ReactNode;
  permissions: {
    id: string;
    label: string;
    enabled: boolean;
  }[];
}

const mockRoles: Role[] = [
  {
    id: 'admin',
    name: 'Administrator',
    icon: <Key size={16} />,
    permissions: [
      { id: '1', label: 'Global Settings', enabled: true },
      { id: '2', label: 'Manage Users', enabled: true },
      { id: '3', label: 'View Finances', enabled: true },
    ]
  },
  {
    id: 'ministry',
    name: 'Ministry Leader',
    icon: <Heart size={16} />,
    permissions: [
      { id: '4', label: 'Manage Ministries', enabled: false },
      { id: '5', label: 'Create Events', enabled: true },
      { id: '6', label: 'Run Own Reports', enabled: true },
    ]
  },
  {
    id: 'member',
    name: 'Member',
    icon: <Users size={16} />,
    permissions: [
      { id: '7', label: 'Register for Events', enabled: true },
      { id: '8', label: 'View Directory', enabled: true },
      { id: '9', label: 'Manage Own Profile', enabled: true },
    ]
  }
];

export function SettingsView() {
  const [roles, setRoles] = useState<Role[]>(mockRoles);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newRoleChecks, setNewRoleChecks] = useState([true, true, true, false]);
  const [churchSettings, setChurchSettings] = useState<ChurchSettings | null>(null);
  const [userProfile, setUserProfile] = useState<any>(null); // Replace with actual User interface
  const [isLoading, setIsLoading] = useState(true);

  React.useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true);
        const [settings, profile] = await Promise.all([
          adminService.getSettings(),
          adminService.getCurrentUser()
        ]);
        setChurchSettings(settings);
        setUserProfile(profile);
      } catch (err) {
        console.error('Failed to load settings data', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const togglePermission = (roleId: string, permId: string) => {
    setRoles(roles.map((r: Role) => {
      if (r.id === roleId) {
        return {
          ...r,
          permissions: r.permissions.map((p: any) => 
            p.id === permId ? { ...p, enabled: !p.enabled } : p
          )
        };
      }
      return r;
    }));
  };

  const toggleNewRoleCheck = (index: number) => {
    const newChecks = [...newRoleChecks];
    newChecks[index] = !newChecks[index];
    setNewRoleChecks(newChecks);
  };

  return (
    <div className="settings-view">
      <h1 className="page-title">System Settings</h1>

      <div className="dashboard-grid">
        
        {/* Left Column */}
        <div className="left-col">
          <div className="glass-card user-profile-card">
            <Pencil className="edit-icon-top" size={16} />
            <h3 className="card-header">User Profile</h3>
            
            {isLoading ? (
              <div style={{ padding: '2rem', textAlign: 'center' }}>Loading profile...</div>
            ) : (
              <>
                <div className="profile-main">
                  <img src={userProfile?.avatar_url || "https://i.pravatar.cc/150?img=11"} alt={userProfile?.full_name || 'User'} />
                  <div className="profile-info">
                    <h2>{userProfile?.full_name || 'Anonymous User'}</h2>
                    <p>{userProfile?.role || 'Member'}</p>
                    <div className="upload-link">
                      <Upload size={12} /> Upload Image
                    </div>
                  </div>
                </div>

                <div className="profile-details">
                  <div className="pd-row">
                    <span className="pd-label">Email</span>
                    <span className="pd-value">{userProfile?.email || 'N/A'}</span>
                  </div>
                  <div className="pd-row">
                    <span className="pd-label">Username</span>
                    <span className="pd-value">{userProfile?.username || 'N/A'}</span>
                  </div>
                  <div className="pd-row">
                    <span className="pd-label">Date of Birth</span>
                    <span className="pd-value">{userProfile?.date_of_birth || 'N/A'}</span>
                  </div>
                  <div className="pd-row">
                    <span className="pd-label">Timezone</span>
                    <span className="pd-value">America/New_York (Static)</span>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="glass-card activity-log-card">
            <h3 className="card-header" style={{ marginBottom: 0 }}>Recent Activity Log</h3>
            
            <div className="timeline">
              <div className="timeline-item">
                <div className="tl-icon"><User /></div>
                <div className="tl-content">Pastor Chen added role<br/>'Sunday School Lead'</div>
                <div className="tl-time">5m ago</div>
              </div>
              <div className="timeline-item">
                <div className="tl-icon"><SettingsIcon /></div>
                <div className="tl-content">System updated to<br/>v2.5.1</div>
                <div className="tl-time">5m ago</div>
              </div>
              <div className="timeline-item">
                <div className="tl-icon"><User /></div>
                <div className="tl-content">Pastor Chen added role<br/>'Sunday School Lead'</div>
                <div className="tl-time">3m ago</div>
              </div>
              <div className="timeline-item">
                <div className="tl-icon"><RefreshCw /></div>
                <div className="tl-content">System updated to v2.5.1</div>
                <div className="tl-time">2m ago</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="right-col">
          
          <div className="top-row-cards">
            <div className="glass-card church-details-card">
              <h3 className="card-header">Church Details</h3>
              {isLoading ? (
                <div style={{ padding: '2rem', textAlign: 'center' }}>Loading details...</div>
              ) : (
                <div className="cd-info">
                  <div><span className="label">Church Name</span> <span className="value">{churchSettings?.church_name || 'Grace Community'}</span></div>
                  <div style={{ marginTop: '8px' }}><span className="label">Address</span> <span className="value">{churchSettings?.church_address || '123 Faith Lane'}</span></div>
                  <div style={{ marginTop: '8px' }}><span className="label">Phone</span> <span className="value">{churchSettings?.church_phone || '(555) 123-4567'}</span></div>
                  <div style={{ marginTop: '8px' }}><span className="label">Website</span> <span className="value">{churchSettings?.church_website || 'www.gracech.org'}</span></div>
                </div>
              )}
              <button className="btn-gold" style={{ marginTop: 'auto' }}>Edit details</button>
            </div>

            <div className="glass-card ministries-card">
              <h3 className="card-header">Ministries at a Glance</h3>
              <div className="stats-grid">
                <div className="stat-box">
                  <h3><Users /> 18</h3>
                  <p>Active<br/>Ministries</p>
                </div>
                <div className="stat-box">
                  <h3><UserPlus /> 45</h3>
                  <p>Registered<br/>Families</p>
                </div>
                <div className="stat-box" style={{ gridColumn: 'span 2', marginTop: '10px' }}>
                  <h3><Clock /> 110h/wk</h3>
                  <p>Volunteer Hours</p>
                </div>
              </div>
              <div className="mock-circle-chart"></div>
            </div>
          </div>

          <div className="glass-card roles-card">
            <div className="roles-header">
              <h3 className="card-header" style={{ margin: 0 }}>Roles & Permissions</h3>
              <button className="btn-outline-gold" onClick={() => setIsModalOpen(true)}>
                <Plus size={14} /> Add Role
              </button>
            </div>

            <div className="role-list">
              {roles.map((role: Role) => (
                <div key={role.id} className="role-card">
                  <div className="role-card-header">
                    <div>
                      <h4>{role.name}</h4>
                    </div>
                    <button className="btn-icon" title="Edit role">
                      <Pencil size={16} />
                    </button>
                  </div>
                  <div className="role-permissions">
                    {role.permissions.map((perm: any) => (
                      <div className="perm-item" key={perm.id}>
                        <span className="perm-label">
                          {perm.label}
                          <br />
                          <span className="perm-sub">Click to toggle</span>
                        </span>
                        <div 
                          className={`toggle ${perm.enabled ? 'on' : ''}`}
                          onClick={() => togglePermission(role.id, perm.id)}
                        ></div>
                      </div>
                    ))}
                  </div>
                  <div className="role-actions">
                    <Pencil />
                    <Trash2 />
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>

      {isModalOpen && (
        <div className="role-modal-overlay">
          <div className="role-modal">
            <div className="modal-header">
              <h2>New Role</h2>
              <X size={20} onClick={() => setIsModalOpen(false)} />
            </div>

            <div className="form-group">
              <label>Role Name</label>
              <input type="text" className="form-input" defaultValue="Sunday School Lead" />
            </div>

            <div className="checkbox-grid">
              <div className="check-item" onClick={() => toggleNewRoleCheck(0)}>
                <div className={`custom-check ${newRoleChecks[0] ? 'checked' : ''}`}>
                  {newRoleChecks[0] && <Check />}
                </div>
                <span>Manage SS Roster<br/>Plans</span>
              </div>
              <div className="check-item" onClick={() => toggleNewRoleCheck(1)}>
                <div className={`custom-check ${newRoleChecks[1] ? 'checked' : ''}`}>
                  {newRoleChecks[1] && <Check />}
                </div>
                <span>Create SS Lesson<br/>Plans</span>
              </div>
              <div className="check-item" onClick={() => toggleNewRoleCheck(2)}>
                <div className={`custom-check ${newRoleChecks[2] ? 'checked' : ''}`}>
                  {newRoleChecks[2] && <Check />}
                </div>
                <span>View Global Finances</span>
              </div>
              <div className="check-item" onClick={() => toggleNewRoleCheck(3)}>
                <div className={`custom-check ${newRoleChecks[3] ? 'checked' : ''}`}>
                  {newRoleChecks[3] && <Check />}
                </div>
                <span>Communicate with<br/>Parents</span>
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Description</label>
              <input type="text" className="form-input" defaultValue="Assign specific abilities to this role." />
            </div>

            <div className="modal-actions">
              <button 
                className="btn-gold" 
                style={{ flex: 1.5 }}
                onClick={() => setIsModalOpen(false)}
              >
                Create Role
              </button>
              <button 
                className="btn-cancel"
                onClick={() => setIsModalOpen(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
