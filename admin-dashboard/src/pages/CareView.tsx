import React, { useState, useEffect } from 'react';
import { 
  Users, FolderOpen, Plus, Search, 
  Filter, ChevronDown, ChevronLeft, ChevronRight,
  Activity, Heart, FileText, Mail, Phone, Calendar
} from 'lucide-react';
import { careService } from '../api/services/care.service';
import type { CareResponse } from '../api/services/care.service';
import './CareView.css';

// Types
export interface CareLeader {
  id: string;
  name: string;
  avatarUrl: string;
}

interface CareRequest {
  id: string;
  requesterName: string;
  requesterAvatar: string;
  type: 'Prayer' | 'Care';
  subType: string;
  dateSubmitted: string;
  summary: string;
  assignedLeader: CareLeader | null;
  status: 'NEW' | 'IN-PROGRESS' | 'NEEDS LEADER';
}

// Mock Data
const MOCK_REQUESTS: CareRequest[] = [
  {
    id: '1',
    requesterName: 'Alice Green',
    requesterAvatar: 'https://i.pravatar.cc/150?img=5',
    type: 'Prayer',
    subType: 'Healing',
    dateSubmitted: 'Sep 20, 2024',
    summary: 'For speedy recovery after knee surgery her surgery on Sept 22.',
    assignedLeader: { id: 'l1', name: 'Elder Sarah Chen', avatarUrl: 'https://i.pravatar.cc/150?img=9' },
    status: 'NEW'
  },
  {
    id: '2',
    requesterName: 'Robert Blake',
    requesterAvatar: 'https://i.pravatar.cc/150?img=11',
    type: 'Care',
    subType: 'Hospital Visit',
    dateSubmitted: 'Sep 18, 2024',
    summary: 'Visiting Elder in St. Jude hospital. Family visiting from out of town.',
    assignedLeader: { id: 'l2', name: 'Pastor John Doe', avatarUrl: 'https://i.pravatar.cc/150?img=12' },
    status: 'IN-PROGRESS'
  },
  {
    id: '3',
    requesterName: 'Maria',
    requesterAvatar: 'https://i.pravatar.cc/150?img=1',
    type: 'Prayer',
    subType: 'Financial',
    dateSubmitted: 'Sep 21, 2024',
    summary: 'Seeking financial guidance and job after knee surgery on Sept 22.',
    assignedLeader: null,
    status: 'NEEDS LEADER'
  },
  {
    id: '4',
    requesterName: 'Tom Hanks',
    requesterAvatar: 'https://i.pravatar.cc/150?img=60',
    type: 'Prayer',
    subType: 'Family',
    dateSubmitted: 'Sep 21, 2024',
    summary: 'Prayer for family reconciliation.',
    assignedLeader: null,
    status: 'NEEDS LEADER'
  },
  {
    id: '5',
    requesterName: 'Emma Watson',
    requesterAvatar: 'https://i.pravatar.cc/150?img=43',
    type: 'Care',
    subType: 'Meals',
    dateSubmitted: 'Sep 22, 2024',
    summary: 'Need meal train setup after giving birth to a baby boy.',
    assignedLeader: null,
    status: 'NEW'
  }
];

// Helper to map DB status to UI format
const mapStatus = (dbStatus: string) => {
  switch (dbStatus?.toLowerCase()) {
    case 'open':
    case 'new': 
      return 'NEW';
    case 'in_progress':
      return 'IN-PROGRESS';
    case 'resolved':
      return 'RESOLVED';
    default:
      return 'NEEDS LEADER';
  }
};

// Map backend CareResponse to CareRequest UI format
const mapToUI = (data: CareResponse[]): CareRequest[] => {
  return data.map(req => ({
    id: req.id,
    requesterName: req.requester_name || 'Unknown',
    requesterAvatar: req.requester_avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(req.requester_name || 'U')}&background=random`,
    type: req.case_type as 'Prayer' | 'Care',
    subType: req.sub_type || '',
    dateSubmitted: new Date(req.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    summary: req.description || 'No description provided.',
    assignedLeader: req.assigned_leader ? {
      id: req.assigned_leader.id,
      name: req.assigned_leader.name,
      avatarUrl: req.assigned_leader.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(req.assigned_leader.name)}&background=random`
    } : null,
    status: mapStatus(req.status) as any
  }));
};

export const CareView: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [requests, setRequests] = useState<CareRequest[]>(MOCK_REQUESTS);
  const [selectedRequest, setSelectedRequest] = useState<CareRequest | null>(MOCK_REQUESTS[0] || null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchCareCases = async () => {
      try {
        setLoading(true);
        const data = await careService.getAllCareCases();
        const mapped = mapToUI(data);
        if (mapped.length > 0) {
          setRequests(mapped);
          setSelectedRequest(mapped[0]);
        }
      } catch (err: any) {
        console.error('Failed to load care cases', err);
        setError('Failed to load care data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchCareCases();
  }, []);

  if (loading) return <div className="care-dashboard" style={{ padding: '2rem' }}>Loading care cases...</div>;
  if (error) return <div className="care-dashboard" style={{ padding: '2rem', color: 'red' }}>{error}</div>;

  const totalRequests = requests.length;
  const activeCases = requests.filter(r => r.status === 'IN-PROGRESS').length;

  return (
    <div className="care-dashboard">
      
      {/* Top Section */}
      <div className="top-section">
        <div className="welcome-area">
          <div className="page-title">
            <h1>Care & Prayer</h1>
          </div>
          <div className="kpi-row">
            <div className="kpi-item">
              <div className="kpi-value"><Users size={24} /> {totalRequests}</div>
              <div className="kpi-label">Total Prayer Requests</div>
            </div>
            <div className="kpi-item">
              <div className="kpi-value"><Activity size={24} /> {activeCases}</div>
              <div className="kpi-label">Active Care Cases</div>
            </div>
            <div className="kpi-item">
              <div className="kpi-value"><FolderOpen size={24} /> {totalRequests - activeCases}</div>
              <div className="kpi-label">Follow-Up Tasks</div>
            </div>
          </div>
        </div>

        <div className="action-area">
          <button className="btn-add">
            <Plus size={18} /> Add Prayer Request
          </button>
          
          <div className="search-row">
            <div className="search-box">
              <Search size={16} />
              <input 
                type="text" 
                placeholder="Search requests, members, or leaders..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <button className="btn-filter">
              <Filter size={16} /> Filters <ChevronDown size={12} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="content-grid">
        
        {/* Left Column: Table */}
        <div className="table-container">
          <div className="table-header-title">ACTIVE PRAYER & CARE REQUESTS ({requests.length} Total)</div>
          
          <table>
            <thead>
              <tr>
                <th>Requester</th>
                <th>Request Type</th>
                <th>Date Submitted</th>
                <th>Summary</th>
                <th>Assigned Leader</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {requests.map(req => (
                <tr 
                  key={req.id} 
                  className={selectedRequest?.id === req.id ? 'active-row' : ''}
                  onClick={() => setSelectedRequest(req)}
                >
                  <td>
                    <div className="user-cell">
                      <img src={req.requesterAvatar} alt={req.requesterName} />
                      {req.requesterName}
                    </div>
                  </td>
                  <td>
                    <div className="type-cell">
                      {req.type === 'Prayer' ? <Activity size={16} /> : <Heart size={16} />}
                      <div className="type-text">
                        <span>{req.type}</span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{req.subType}</span>
                      </div>
                    </div>
                  </td>
                  <td>{req.dateSubmitted}</td>
                  <td>
                    <div className="summary-cell">{req.summary}</div>
                  </td>
                  <td>
                    {req.assignedLeader ? (
                      <div className="leader-cell">
                        <img src={req.assignedLeader.avatarUrl} alt={req.assignedLeader.name} />
                        <div className="leader-info">
                          <span>{req.assignedLeader.name}</span>
                          <span>Reassign <ChevronDown size={10} /></span>
                        </div>
                      </div>
                    ) : (
                      <div className="leader-info">
                        <span style={{ color: 'var(--text-muted)' }}>(Unassigned)</span>
                      </div>
                    )}
                  </td>
                  <td>
                    <div className={`status-badge ${req.status === 'NEW' ? 'new' : req.status === 'IN-PROGRESS' ? 'progress' : 'needs'}`}>
                      {req.status}
                    </div>
                  </td>
                  <td>
                    <div className="action-cell">
                      <button className="btn-dropdown" onClick={(e) => e.stopPropagation()}>
                        Assign <ChevronDown size={10} />
                      </button>
                      <button className="btn-icon-sm" onClick={(e) => e.stopPropagation()}>
                        <FileText size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="pagination">
            <ChevronLeft size={16} />
            <div className="page-num active">1</div>
            <div className="page-num">2</div>
            <ChevronRight size={16} />
          </div>
        </div>

        {/* Right Column: Detail Sidebar */}
        <div className="detail-sidebar">
          <div className="detail-header">REQUEST DETAILS & QUICK FOLLOW-UP</div>
          
          {selectedRequest ? (
            <>
              <div className="profile-card">
                <img src={selectedRequest.requesterAvatar} alt={selectedRequest.requesterName} />
                <div className="profile-info">
                  <h3>{selectedRequest.requesterName}</h3>
                  <p>Member since 2018</p>
                </div>
              </div>

              <div className="detail-grid">
                <div className="detail-label">Type</div>
                <div>{selectedRequest.type} ({selectedRequest.subType})</div>
                
                <div className="detail-label">Summary</div>
                <div>{selectedRequest.summary}</div>
                
                <div className="detail-label">Submitted</div>
                <div>{selectedRequest.dateSubmitted}</div>
              </div>

          <div className="follow-up-section">
            <h4>Current Follow-Up Plan</h4>
            
            <div className="plan-list">
              <div className="plan-item active">
                <div className="plan-left">
                  <div className="custom-check" style={{ borderColor: 'var(--text-dark)' }}>
                    {/* Checkmark placeholder */}
                    <div style={{ width: 8, height: 8, background: 'var(--text-dark)', borderRadius: 2 }}></div>
                  </div>
                  <span>Send a Message of Encouragement</span>
                </div>
                <span className="plan-date">Sep 21</span>
              </div>
              
              <div className="plan-item">
                <div className="plan-left">
                  <div className="custom-check"></div>
                  <span>Schedule Phone Call</span>
                </div>
                <span className="plan-date">Sep 23</span>
              </div>
              
              <div className="plan-item">
                <div className="plan-left">
                  <div className="custom-check"></div>
                  <span>Mark as Handled</span>
                </div>
                <span className="plan-date">Sep 25</span>
              </div>
            </div>

              <div className="quick-actions">
                <h4>Quick Follow-up Actions</h4>
                <div className="action-list">
                  <button className="btn-quick">
                    <Mail size={16} /> Send Email / SMS
                  </button>
                  <button className="btn-quick">
                    <Phone size={16} /> Log Call
                  </button>
                  <button className="btn-quick">
                    <Calendar size={16} /> Schedule Visit
                  </button>
                </div>
              </div>
            </div>
          </>
        ) : (
           <div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Select a request to view details</div>
        )}
        </div>
      </div>
    </div>
  );
};

export default CareView;
