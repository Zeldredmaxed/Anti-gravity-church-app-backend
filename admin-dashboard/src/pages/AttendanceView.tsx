import React, { useState, useEffect } from 'react';
import { attendanceService } from '../api/services/attendance.service';
import type { Service, AttendanceRecord, AttendanceTrend } from '../api/services/attendance.service';
import { membersService } from '../api/services/members.service';
import type { Member } from '../api/services/members.service';
import './AttendanceView.css';

export const AttendanceView: React.FC = () => {
    const [services, setServices] = useState<Service[]>([]);
    const [selectedServiceId, setSelectedServiceId] = useState<number | null>(null);
    const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
    
    const [members, setMembers] = useState<Member[]>([]);
    const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>([]);
    const [trends, setTrends] = useState<AttendanceTrend[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        if (selectedServiceId) {
            loadAttendanceData(selectedServiceId, selectedDate);
        }
    }, [selectedServiceId, selectedDate]);

    const loadInitialData = async () => {
        setIsLoading(true);
        try {
            const [fetchedServices, fetchedMembers, fetchedTrends] = await Promise.all([
                attendanceService.getServices(),
                membersService.getMembers({ per_page: 100 }),
                attendanceService.getTrends(5) // Get last 5 weeks for the chart
            ]);
            setServices(fetchedServices);
            setMembers(fetchedMembers.items);
            setTrends(fetchedTrends);
            
            if (fetchedServices.length > 0) {
                setSelectedServiceId(fetchedServices[0].id);
            }
        } catch (error) {
            console.error('Error loading initial attendance data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const loadAttendanceData = async (serviceId: number, date: string) => {
        try {
            const records = await attendanceService.getServiceAttendance(serviceId, date);
            setAttendanceRecords(records);
        } catch (error) {
            console.error('Error loading attendance records:', error);
        }
    };

    const handleServiceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSelectedServiceId(Number(e.target.value));
    };

    const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSelectedDate(e.target.value);
    };

    const handleToggleAttendance = async (memberId: number, isPresent: boolean) => {
        if (!selectedServiceId) return;

        try {
            if (isPresent) {
                // Check in
                await attendanceService.checkIn({
                    service_id: selectedServiceId,
                    member_id: memberId,
                    date: selectedDate
                });
            } else {
                // Find record and check out conceptually, or delete. 
                // The current API only has checkout, not delete. But we will just reload for now
                const record = attendanceRecords.find(r => r.member_id === memberId);
                if (record) {
                    await attendanceService.checkOut(record.id);
                }
            }
            // Reload to get latest status
            loadAttendanceData(selectedServiceId, selectedDate);
        } catch (error) {
            console.error("Error toggling attendance", error);
        }
    };

    // Calculate derived data
    const presentMemberIds = new Set(attendanceRecords.map(r => r.member_id).filter(id => id !== null) as number[]);
    const attendeesList = members.map(m => {
        const isPresent = presentMemberIds.has(m.id);
        return {
            id: m.id,
            name: `${m.first_name} ${m.last_name}`,
            family: 'N/A', // Placeholder since address is not available in basic Member type
            group: m.membership_status || 'N/A',
            phone: m.phone,
            email: m.email,
            status: isPresent ? 'present' : 'absent',
            selected: false,
        };
    });

    const totalPresent = attendanceRecords.length;
    const totalAbsent = attendeesList.filter(a => a.status === 'absent').length;
    const totalVisitors = attendanceRecords.filter(r => r.is_first_time_guest).length;
    const attendancePercentage = attendeesList.length > 0 ? Math.round((totalPresent / attendeesList.length) * 100) : 0;

    return (
        <div className="attendance-view fade-in">
            <div className="page-header">
                <h1 className="page-title">Sunday Service Attendance</h1>
                
                <div className="controls-row">
                    <div className="left-controls">
                        <div className="input-group">
                            <select 
                                className="control-input" 
                                style={{ width: '220px', appearance: 'none', background: 'transparent', border: '1px solid rgba(255,255,255,0.4)' }}
                                value={selectedServiceId || ''}
                                onChange={handleServiceChange}
                            >
                                {services.map(s => (
                                    <option key={s.id} value={s.id} style={{color: '#000'}}>{s.name}</option>
                                ))}
                            </select>
                        </div>
                        
                        <div className="control-input">
                            <i className="fa-regular fa-calendar" style={{ color: '#666' }}></i>
                            <input 
                                type="date"
                                value={selectedDate}
                                onChange={handleDateChange}
                                style={{ border: 'none', background: 'transparent', outline: 'none' }}
                            />
                        </div>

                        <div className="control-input search-bar">
                            <i className="fa-solid fa-magnifying-glass" style={{ color: '#999' }}></i>
                            <input type="text" placeholder="Search member..." />
                        </div>
                    </div>

                    <div className="right-controls">
                        <button className="btn btn-gray"><i className="fa-solid fa-plus"></i> Add Visitor</button>
                        <button className="btn btn-gray">Bulk Present</button>
                        <button className="btn btn-gold">Save Attendance</button>
                        <button className="btn btn-gray">Export Report</button>
                    </div>
                </div>
            </div>

            <div className="kpi-row">
                <div className="glass-panel kpi-card">
                    <div className="kpi-info">
                        <h3>Present</h3>
                        <div className="kpi-number">{totalPresent} <span>{attendancePercentage}%</span></div>
                    </div>
                    <div className="kpi-icon-wrapper" style={{ background: '#f0e3ce' }}><i className="fa-solid fa-hands-clapping" style={{ color: '#d4a345' }}></i></div>
                </div>
                <div className="glass-panel kpi-card">
                    <div className="kpi-info">
                        <h3 style={{ color: '#555' }}>Absent</h3>
                        <div className="kpi-number" style={{ color: '#a0a0a0' }}>{totalAbsent} <span>{100 - attendancePercentage}%</span></div>
                    </div>
                    <div className="kpi-icon-wrapper" style={{ background: 'transparent', borderColor: '#d4a345', color: '#a0a0a0' }}><i className="fa-solid fa-chair" style={{ color: '#a0a0a0' }}></i></div>
                </div>
                <div className="glass-panel kpi-card">
                    <div className="kpi-info">
                        <h3 style={{ color: '#555' }}>Visitors</h3>
                        <div className="kpi-number" style={{ color: '#d4a345' }}>{totalVisitors}</div>
                    </div>
                    <div className="kpi-icon-wrapper" style={{ background: '#f0e3ce' }}><i className="fa-solid fa-handshake" style={{ color: '#d4a345' }}></i></div>
                </div>
            </div>

            <div className="main-grid">
                
                <div className="glass-panel table-section">
                    <h2 className="section-title">Attendance Table</h2>
                    
                    {isLoading ? (
                        <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>Loading...</div>
                    ) : (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th><div className="custom-checkbox"></div></th>
                                    <th><div style={{ background: 'rgba(255,255,255,0.8)', border: '1px solid #ddd', padding: '6px 12px', borderRadius: '20px', display: 'inline-block', fontSize: '12px' }}>Attendance <i className="fa-solid fa-chevron-down" style={{ fontSize: '10px' }}></i></div></th>
                                    <th>Status <i className="fa-solid fa-circle-check" style={{ color: 'var(--accent-gold)' }}></i></th>
                                    <th>Member Name <i className="fa-solid fa-sort sort-icon"></i></th>
                                    <th>Info <i className="fa-solid fa-sort sort-icon"></i></th>
                                    <th>Contact <i className="fa-solid fa-sort sort-icon"></i></th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {attendeesList.map(a => (
                                    <tr key={a.id} className={a.selected ? 'row-highlight' : ''}>
                                        <td>
                                            <div className="custom-checkbox"></div>
                                        </td>
                                        <td>
                                            <div className="status-toggle">
                                                <div 
                                                    className={`status-btn ${a.status === 'present' ? 'active-check' : 'inactive'}`}
                                                    onClick={() => handleToggleAttendance(a.id, true)}
                                                    style={{ cursor: 'pointer' }}
                                                >
                                                    <i className="fa-solid fa-check"></i>
                                                </div>
                                                <div 
                                                    className={`status-btn ${a.status === 'absent' ? 'active-x' : 'inactive'}`}
                                                    onClick={() => handleToggleAttendance(a.id, false)}
                                                    style={{ cursor: 'pointer' }}
                                                >
                                                    <i className="fa-solid fa-xmark"></i>
                                                </div>
                                            </div>
                                        </td>
                                        <td>
                                            {a.status === 'present' 
                                                ? <i className="fa-solid fa-circle-check" style={{ color: 'var(--accent-gold)' }}></i>
                                                : <i className="fa-solid fa-circle-xmark" style={{ color: '#8a8d91' }}></i>
                                            }
                                        </td>
                                        <td style={{ fontWeight: 500 }}>{a.name}</td>
                                        <td>{a.family}</td>
                                        <td>{a.phone || a.email || 'N/A'}</td>
                                        <td><i className="fa-solid fa-ellipsis" style={{ cursor: 'pointer', color: '#666' }}></i></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

                <div className="flex-col" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    
                    <div className="glass-panel chart-card">
                        <h3>Sunday Attendance Trend</h3>
                        <div className="bar-chart-container">
                            {trends.length === 0 ? (
                                <p style={{ textAlign: 'center', color: '#666', marginTop: '20px' }}>No trend data available</p>
                            ) : (
                                trends.map((trend, i) => {
                                    // Scale height based on max value
                                    const maxVal = Math.max(...trends.map(t => t.total), 1);
                                    const heightPercent = (trend.total / maxVal) * 100;
                                    const dateLabel = trend.period.split(' to ')[0].substring(5, 10);
                                    
                                    return (
                                        <div key={i} className="bar-wrapper">
                                            <span className="bar-label-top">{trend.total}</span>
                                            <div className="bar" style={{ height: `${Math.max(10, heightPercent)}%` }}></div>
                                            <span className="bar-label-bottom">{dateLabel}</span>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>

                    <div className="glass-panel chart-card">
                        <h3>Overall Service Attendance</h3>
                        <div className="donut-container">
                            <svg width="140" height="140" viewBox="0 0 140 140">
                                <circle cx="70" cy="70" r="60" fill="none" stroke="#e0e0e0" strokeWidth="12" />
                                <circle 
                                    cx="70" cy="70" r="60" fill="none" stroke="#d4a345" strokeWidth="12" 
                                    strokeDasharray={`${(attendancePercentage / 100) * 377} 377`} 
                                    strokeLinecap="round" transform="rotate(-90 70 70)" 
                                />
                            </svg>
                            <div className="donut-text">
                                <h2>{attendancePercentage}%</h2>
                                <p>Present</p>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};
