import React, { useState, useEffect } from 'react';
import './GivingView.css';
import { givingService, type Donation } from '../api/services/giving.service';

export const GivingView: React.FC = () => {
    const [donations, setDonations] = useState<Donation[]>([]);
    const [loading, setLoading] = useState(true);
    const [totalGiving, setTotalGiving] = useState(0);

    useEffect(() => {
        async function loadGiving() {
            try {
                setLoading(true);
                const data = await givingService.getDonations();
                setDonations(data.items);
                setTotalGiving(data.total_amount);
            } catch (error) {
                console.error("Failed to load giving data:", error);
            } finally {
                setLoading(false);
            }
        }
        loadGiving();
    }, []);

    // Helper functions for UI
    const getMethodIcon = (method: string) => {
        const _method = method?.toLowerCase() || '';
        if (_method.includes('card') || _method.includes('visa') || _method.includes('mastercard')) return 'cc-mastercard mc';
        if (_method.includes('paypal')) return 'cc-paypal pp';
        if (_method.includes('check')) return 'money-check check';
        if (_method.includes('cash')) return 'money-bill-1 check';
        if (_method.includes('ach') || _method.includes('bank')) return 'building-columns ach';
        return 'credit-card mc';
    };

    return (
        <div className="giving-view fade-in">
            <h1 className="page-title">Giving</h1>

            <div className="kpi-grid">
                <div className="kpi-card">
                    <div className="kpi-badge">15%</div>
                    <div className="kpi-title">Total Giving</div>
                    <div className="kpi-value">${loading ? '...' : Number(totalGiving).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2})}</div>
                    <div className="progress-bar"><div className="progress-fill" style={{ width: '85%' }}></div></div>
                </div>
                {/* Metrics placeholders since direct categorization isn't fully separated from API right now */}
                <div className="kpi-card">
                    <div className="kpi-title">Tithe</div>
                    <div className="kpi-value">$9,100</div>
                    <div className="progress-bar"><div className="progress-fill" style={{ width: '45%' }}></div></div>
                </div>
                <div className="kpi-card">
                    <div className="kpi-title">Offering</div>
                    <div className="kpi-value">$4,950</div>
                </div>
                <div className="kpi-card">
                    <div className="kpi-title">Missions</div>
                    <div className="kpi-value">$4,400</div>
                </div>
            </div>

            <div className="lower-layout">
                <div className="left-column">
                    
                    <div className="chart-card">
                        <div className="chart-header">
                            <div className="chart-title">Giving Over Time</div>
                            <div className="chart-filters">
                                <span>Weekly</span> | <span className="active">Monthly</span> | <span>Yearly</span>
                            </div>
                        </div>
                        <div className="chart-area">
                            <svg viewBox="0 0 800 100" preserveAspectRatio="none">
                                <defs>
                                    <linearGradient id="chart-gradient" x1="0" x2="0" y1="0" y2="1">
                                        <stop offset="0%" stopColor="#f2c96c" stopOpacity="0.4"/>
                                        <stop offset="100%" stopColor="#f2c96c" stopOpacity="0"/>
                                    </linearGradient>
                                </defs>
                                <path className="chart-fill" d="M0,80 L150,60 L280,40 L380,65 L500,75 L650,45 L800,30 L800,100 L0,100 Z"></path>
                                <path className="chart-line" d="M0,80 L150,60 L280,40 L380,65 L500,75 L650,45 L800,30"></path>
                                <circle className="chart-point" cx="280" cy="40" r="4"></circle>
                            </svg>
                        </div>
                    </div>

                    <div className="table-card">
                        <div className="table-controls">
                            <div className="left-controls">
                                <div className="control-dropdown">Category <i className="fa-solid fa-chevron-down"></i></div>
                                <div className="control-dropdown"><i className="fa-regular fa-calendar" style={{ color: '#9ca3af' }}></i> Oct 22 - 2023 <i className="fa-solid fa-chevron-right" style={{ color: '#9ca3af' }}></i></div>
                            </div>
                            <div className="right-controls">
                                <button className="btn btn-outline">Export Statement</button>
                                <button className="btn btn-solid">New Pledge</button>
                                <button className="btn btn-gold"><i className="fa-solid fa-plus"></i> Add Donation</button>
                            </div>
                        </div>

                        <table>
                            <thead>
                                <tr>
                                    <th>Status <i className="fa-solid fa-sort"></i></th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan={8} style={{textAlign: 'center', padding: '20px'}}>Loading transactions...</td></tr>
                                ) : donations.length === 0 ? (
                                    <tr><td colSpan={8} style={{textAlign: 'center', padding: '20px'}}>No transactions found.</td></tr>
                                ) : (
                                    donations.map((tx, idx) => (
                                        <tr key={tx.id}>
                                            <td><div className="custom-checkbox"></div></td>
                                            <td>
                                                <div className="donor-cell">
                                                    <img src={`https://i.pravatar.cc/150?img=${(idx % 70) + 1}`} alt="Donor" />
                                                    {tx.donor_name || 'Anonymous'}
                                                </div>
                                            </td>
                                            <td style={{textTransform: 'capitalize'}}>{tx.donation_type}</td>
                                            <td>${Number(tx.amount).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2})}</td>
                                            <td>{new Date(tx.date).toLocaleDateString()}</td>
                                            <td>
                                                <i className={`fa-solid fa-${getMethodIcon(tx.payment_method)} method-icon`}></i>
                                                <span style={{marginLeft: '8px', textTransform: 'capitalize'}}>{tx.payment_method}</span>
                                            </td>
                                            <td>{tx.fund_name || '-'}</td>
                                            <td>
                                                <span className={`status-badge status-completed`}>Completed</span>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>

                        <div className="table-footer">
                            <div className="pagination">
                                <i className="fa-solid fa-chevron-left" style={{ color: '#9ca3af' }}></i>
                                <span>1</span>
                                <i className="fa-solid fa-chevron-right" style={{ color: '#9ca3af' }}></i>
                            </div>
                            <div>Showing {donations.length > 0 ? 1 : 0}-{donations.length > 10 ? 10 : donations.length} of {loading ? '...' : (donations.length || 0)} transactions</div>
                        </div>

                    </div>
                </div>

                <div className="sidebar-card">
                    <div className="form-header">Add New Donation</div>
                    <div className="form-body">
                        
                        <div className="form-row">
                            <div className="form-group">
                                <label>Donor</label>
                                <div className="input-box">John Smith <div style={{display:'flex', gap:'8px'}}><i className="fa-solid fa-magnifying-glass"></i><i className="fa-solid fa-chevron-down"></i></div></div>
                            </div>
                            <div className="form-group">
                                <label>Date</label>
                                <div className="input-box">Oct 22, 2023 <i className="fa-regular fa-calendar"></i></div>
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label>Amount</label>
                                <div className="input-box">$150.00</div>
                                
                                <label style={{ marginTop: '8px' }}>Category</label>
                                <div className="mock-dropdown">
                                    <div className="md-item">Tithe</div>
                                    <div className="md-item">Offering</div>
                                    <div className="md-item selected">Missions <i className="fa-solid fa-check"></i></div>
                                    <div className="md-item">Pledge</div>
                                    <div className="md-item">Gift</div>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Method</label>
                                <div className="mock-dropdown">
                                    <div className="md-item">Mastercard</div>
                                    <div className="md-item">Visa</div>
                                    <div className="md-item">Check</div>
                                    <div className="md-item selected">Cash <i className="fa-solid fa-check"></i></div>
                                    <div className="md-item">Paypal</div>
                                </div>
                                
                                <label style={{ marginTop: '8px' }}>Fund</label>
                                <div className="mock-dropdown">
                                    <div className="md-item selected">General Fund</div>
                                    <div className="md-item">Building Fund</div>
                                    <div className="md-item">Benevolence</div>
                                </div>
                            </div>
                        </div>

                        <div className="form-group">
                            <label>Notes</label>
                            <div className="input-box" style={{ justifyContent: 'flex-start', color: 'var(--text-muted)', fontWeight: 400 }}>Giving for the local food bank</div>
                        </div>

                        <div className="form-actions">
                            <button className="btn-cancel">Cancel</button>
                            <button className="btn-save"><i className="fa-solid fa-plus"></i> Save Donation</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

