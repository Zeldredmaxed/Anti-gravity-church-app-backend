import React, { useState, useEffect } from 'react';
import { 
  Search, Filter, Plus, ChevronDown, MoreHorizontal, 
  Users, UserCheck, Calendar, X 
} from 'lucide-react';
import './GroupsView.css';
import { groupsService } from '../api/services/groups.service';
import type { GroupResponse, GroupCreate } from '../api/services/groups.service';

export const GroupsView: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [loading, setLoading] = useState(true);

  // Active states for popovers (track by group ID)
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [activeAssignId, setActiveAssignId] = useState<string | null>(null);

  // New Group Form State
  const [newGroupData, setNewGroupData] = useState<GroupCreate>({
    name: '',
    group_type: 'Worship / Music',
    meeting_day: '',
    meeting_time: '',
    description: '',
    is_active: true
  });

  useEffect(() => {
     fetchGroups();
  }, []);

  const fetchGroups = async () => {
     try {
        setLoading(true);
        const data = await groupsService.getGroups();
        setGroups(data);
     } catch (err) {
        console.error("Error fetching groups:", err);
     } finally {
        setLoading(false);
     }
  };

  const handleCreateGroup = async () => {
      try {
          await groupsService.createGroup(newGroupData);
          setIsCreateModalOpen(false);
          setNewGroupData({
            name: '',
            group_type: 'Worship / Music',
            meeting_day: '',
            meeting_time: '',
            description: '',
            is_active: true
          });
          fetchGroups();
      } catch (err) {
          console.error("Error creating group:", err);
          alert("Failed to create group. Check network or permissions.");
      }
  };

  // Close all popovers when clicking outside
  const closeAllPopovers = () => {
    setActiveMenuId(null);
    setActiveAssignId(null);
  };

  const filteredGroups = groups.filter(g => 
    g.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    g.group_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="groups-dashboard fade-in" onClick={closeAllPopovers}>
      
      {/* Page Header */}
      <div className="page-header">
        <div className="page-title">
          <h1>Groups & Teams</h1>
          <div className="breadcrumbs">
            Dashboard / <span>Groups</span>
          </div>
        </div>
        <div className="page-controls">
          <div className="search-input">
            <Search size={18} />
            <input 
              type="text" 
              placeholder="Search groups..." 
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="control-btn white">
            <Filter size={18} /> Filter
            <ChevronDown size={14} />
          </button>
          <button 
            className="control-btn primary" 
            style={{ background: 'var(--accent-gold)', color: 'white', border: 'none' }}
            onClick={(e) => { e.stopPropagation(); setIsCreateModalOpen(true); }}
          >
            <Plus size={18} /> New Group
          </button>
        </div>
      </div>

      {/* Grid Container */}
      <div className="grid-container">
        {loading ? (
            <div style={{ padding: '20px', color: 'var(--text-muted)' }}>Loading groups...</div>
        ) : filteredGroups.length === 0 ? (
            <div style={{ padding: '20px', color: 'var(--text-muted)' }}>No groups found.</div>
        ) : filteredGroups.map(group => {
          const isMenuOpen = activeMenuId === group.id.toString();
          const isAssignOpen = activeAssignId === group.id.toString();

          // Generate placeholder generic avatars based on member_count
          const visibleAvatars = Math.min(group.member_count, 4);
          const remaining = Math.max(0, group.member_count - visibleAvatars);

          return (
            <div className={`group-card ${isAssignOpen ? 'glowing' : ''}`} key={group.id}>
              
              <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 className="card-title">{group.name}</h3>
                  <div className="card-subtitle">
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Users size={14} /> {group.group_type}</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Calendar size={14} /> {group.meeting_day} {group.meeting_time ? `at ${group.meeting_time}` : ''}
                    </span>
                  </div>
                </div>
                
                {/* Action Ellipsis Menu */}
                <div style={{ position: 'relative' }}>
                  <button 
                    className="action-ellipsis"
                    onClick={(e) => {
                      e.stopPropagation();
                      closeAllPopovers();
                      setActiveMenuId(isMenuOpen ? null : group.id.toString());
                    }}
                  >
                    <MoreHorizontal size={18} />
                  </button>
                  
                  {isMenuOpen && (
                    <div className="action-menu" onClick={e => e.stopPropagation()}>
                      <div className="action-item"><Calendar size={14} /> View Schedule</div>
                      <div className="action-item"><Users size={14} /> Manage Members</div>
                      <div className="action-item" style={{ color: 'var(--status-red)' }}>
                        <X size={14} /> Delete Group
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="card-stats">
                <span className="stat-main">{group.member_count} Members</span>
                <span className="stat-sub">Active in this group</span>
              </div>

              <div className="card-footer">
                <div className="avatar-stack">
                  {Array.from({ length: visibleAvatars }).map((_, i) => (
                    <img key={i} src={`https://i.pravatar.cc/150?img=${group.id + i}`} alt="Member" title="Member" />
                  ))}
                  {remaining > 0 && (
                    <div style={{
                      width: '32px', height: '32px', borderRadius: '50%', 
                      background: '#f0f0f0', display: 'flex', alignItems: 'center', 
                      justifyContent: 'center', fontSize: '11px', fontWeight: 500,
                      marginLeft: '-10px', border: '2px solid white', zIndex: 10,
                      color: 'var(--text-muted)'
                    }}>
                      +{remaining}
                    </div>
                  )}
                </div>
              </div>

              {/* Assign Members Button */}
              <button 
                className="btn-assign"
                onClick={(e) => {
                  e.stopPropagation();
                  closeAllPopovers();
                  setActiveAssignId(isAssignOpen ? null : group.id.toString());
                }}
              >
                Assign
              </button>

              {/* Assign Members Popover */}
              {isAssignOpen && (
                 <div className="assign-popover" onClick={e => e.stopPropagation()}>
                  <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-dark)' }}>
                    Assign Members
                  </div>
                  <div className="popover-search">
                    <input type="text" placeholder="Search members..." />
                    <Search size={14} color="var(--text-muted)" />
                  </div>
                  
                  <div className="member-list">
                      <div style={{ padding: '8px', fontSize: '12px', color: '#666' }}>
                          (Member assignment functionality would go here)
                      </div>
                  </div>

                  <div className="popover-actions">
                    <button className="btn-cancel" onClick={() => setActiveAssignId(null)}>Cancel</button>
                    <button className="btn-save" onClick={() => setActiveAssignId(null)}>Save</button>
                  </div>
                </div>
              )}

            </div>
          );
        })}
      </div>

      {/* Create Group Modal */}
      {isCreateModalOpen && (
        <div className="create-modal-overlay">
          <div className="create-modal" style={{ top: '60px', right: '40px' }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Group</h2>
              <button onClick={() => setIsCreateModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            
            <div className="form-group">
              <label>Group Name</label>
              <div className="input-box">
                <input 
                  type="text" 
                  placeholder="e.g. Sunday Worship Team" 
                  style={{ border: 'none', outline: 'none', background: 'transparent', width: '100%' }} 
                  value={newGroupData.name}
                  onChange={e => setNewGroupData({...newGroupData, name: e.target.value})}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Category/Type</label>
                <div className="input-box">
                  <select 
                      style={{ border: 'none', outline: 'none', background: 'transparent', width: '100%', color: 'var(--text-dark)', appearance: 'none' }}
                      value={newGroupData.group_type}
                      onChange={e => setNewGroupData({...newGroupData, group_type: e.target.value})}
                  >
                    <option>Worship / Music</option>
                    <option>Youth / Education</option>
                    <option>Guest Services</option>
                    <option>Small Group</option>
                    <option>Missions</option>
                    <option>Production</option>
                  </select>
                  <ChevronDown size={14} />
                </div>
              </div>
              <div className="form-group">
                <label>Meeting Day</label>
                <div className="input-box">
                  <input 
                      type="text" 
                      placeholder="e.g. Sundays" 
                      style={{ border: 'none', outline: 'none', background: 'transparent', width: '100%' }} 
                      value={newGroupData.meeting_day}
                      onChange={e => setNewGroupData({...newGroupData, meeting_day: e.target.value})}
                  />
                </div>
              </div>
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea 
                  className="input-box" 
                  placeholder="Brief description of this group..." 
                  value={newGroupData.description}
                  onChange={e => setNewGroupData({...newGroupData, description: e.target.value})}
              />
            </div>

            <div className="modal-footer">
              <button type="button" onClick={() => setIsCreateModalOpen(false)}>Cancel</button>
              <button className="btn-create" onClick={handleCreateGroup}>Create Group</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
