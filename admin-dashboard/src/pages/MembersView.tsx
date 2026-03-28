import React, { useState, useEffect } from 'react';
import './MembersView.css';
import { clsx } from 'clsx';
import { membersService, type Member } from '../api/services/members.service';

export function MembersView() {
  const [showModal, setShowModal] = useState(false);
  const [showStatusFilter, setShowStatusFilter] = useState(false);
  const [showExport, setShowExport] = useState(false);
  
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalMembers, setTotalMembers] = useState(0);

  useEffect(() => {
    async function loadMembers() {
      try {
        setLoading(true);
        const data = await membersService.getMembers();
        setMembers(data.items);
        setTotalMembers(data.total);
      } catch (error) {
        console.error("Failed to load members:", error);
      } finally {
        setLoading(false);
      }
    }
    loadMembers();
  }, []);

  return (
    <div className="members-page">
      <h1 className="page-title">Members</h1>

      <div className="kpi-grid">
        <div className="glass-card kpi-card">
          <span className="kpi-title">New Members</span>
          <span className="kpi-value">35</span>
        </div>
        <div className="glass-card kpi-card">
          <span className="kpi-title">Total Members</span>
          <div className="kpi-value">
            {loading ? '...' : totalMembers}
            <div className="progress-container">
              <div className="progress-bar">
                <div className="progress-fill fill-yellow" style={{width: '65%'}}>65%</div>
              </div>
            </div>
          </div>
        </div>
        <div className="glass-card kpi-card">
          <span className="kpi-title">Active Small Groups</span>
          <span className="kpi-value">52</span>
        </div>
        <div className="glass-card kpi-card">
          <span className="kpi-title">Baptism Rate</span>
          <div className="kpi-value">
            78%
            <div className="progress-container">
              <div className="progress-bar">
                <div className="progress-fill fill-dark" style={{width: '78%'}}>78%</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="table-toolbar">
        <div className="toolbar-left">
          <div className="search-wrapper">
            <div className="search-box">
              <i className="fa-solid fa-magnifying-glass"></i>
              <input type="text" placeholder="Search members..." />
            </div>
            <span className="search-hint">*Live search filtering</span>
          </div>

          <div className="filter-dropdown">
            Columns <i className="fa-solid fa-chevron-down"></i>
          </div>

          <div className="filter-dropdown active" onClick={() => setShowStatusFilter(!showStatusFilter)}>
            Membership Status <i className="fa-solid fa-chevron-down"></i>
            {showStatusFilter && (
              <div className="dropdown-menu">
                <div className="dropdown-item">Visitor</div>
                <div className="dropdown-item">Member</div>
                <div className="dropdown-item">Inactive</div>
              </div>
            )}
          </div>

          <div className="filter-dropdown">
            Baptism Status <i className="fa-solid fa-chevron-down"></i>
          </div>
          <div className="filter-dropdown">
            Group <i className="fa-solid fa-chevron-down"></i>
          </div>
          <div className="filter-dropdown">
            Ministry <i className="fa-solid fa-chevron-down"></i>
          </div>
        </div>

        <div className="toolbar-right">
          <button className="btn-outline" onClick={() => setShowModal(true)}>
            <i className="fa-solid fa-plus"></i> Add Member
          </button>
          <div className="btn-outline" onClick={() => setShowExport(!showExport)}>
            <i className="fa-solid fa-download"></i> Export <i className="fa-solid fa-chevron-down"></i>
            {showExport && (
              <div className="export-dropdown">
                <div className="dropdown-item">CSV</div>
                <div className="dropdown-item">PDF</div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="table-container">
        <table className="members-table">
          <thead>
            <tr>
              <th width="40">
                <div className="custom-checkbox"></div>
              </th>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Join Date</th>
              <th>Primary Group</th>
              <th>Ministry</th>
              <th>Baptism Status</th>
              <th>Membership Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={10} style={{textAlign: 'center', padding: '20px'}}>Loading members...</td></tr>
            ) : members.length === 0 ? (
              <tr><td colSpan={10} style={{textAlign: 'center', padding: '20px'}}>No members found.</td></tr>
            ) : (
              members.map((member, i) => (
                <tr key={member.id} className={i % 2 === 0 ? "highlight-light" : "highlight-dark"}>
                  <td>
                    <div className="custom-checkbox"></div>
                  </td>
                  <td>
                    <div className="avatar-cell">
                      <img src={`https://i.pravatar.cc/150?img=${(i % 70) + 1}`} alt="Avatar" /> {member.first_name} {member.last_name}
                    </div>
                  </td>
                  <td>{member.email || '-'}</td>
                  <td>{member.phone || '-'}</td>
                  <td>{member.join_date ? new Date(member.join_date).toLocaleDateString() : '-'}</td>
                  <td>-</td>
                  <td>-</td>
                  <td>
                    <div className="status-pill blue">
                      Unknown <i className="fa-solid fa-chevron-down"></i>
                    </div>
                  </td>
                  <td>
                    <div className="status-pill green" style={{textTransform: 'capitalize'}}>
                      {member.membership_status} <i className="fa-solid fa-chevron-down"></i>
                    </div>
                  </td>
                  <td style={{ position: 'relative' }}>
                    <div className="action-icons">
                      <i className="fa-regular fa-eye"></i>
                      <i className="fa-solid fa-pencil"></i>
                      <i className="fa-regular fa-trash-can"></i>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <div className="page-info">
          Pages: <input type="text" className="page-input" defaultValue="1" /> of {Math.ceil(totalMembers / 50) || 1}
        </div>
        <div className="page-nav">
          <span>
            <i className="fa-solid fa-chevron-left" style={{ fontSize: 10 }}></i> Next{' '}
            <i className="fa-solid fa-chevron-right" style={{ fontSize: 10 }}></i>
          </span>
        </div>
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-body">
            <h2 className="modal-title">Add New Member</h2>

            <div className="form-row">
              <div className="form-group">
                <label>Name</label>
                <input type="text" className="form-input" placeholder="Input" />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input type="text" className="form-input" placeholder="Email" />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Phone</label>
                <input type="text" className="form-input" placeholder="Phone" />
              </div>
              <div className="form-group">
                <label>Date of Birth</label>
                <div className="input-icon">
                  <input type="text" className="form-input" placeholder="Date of Birth" />
                  <i className="fa-regular fa-calendar"></i>
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button className="btn-save" onClick={() => setShowModal(false)}>Save</button>
              <button className="btn-cancel" onClick={() => setShowModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
