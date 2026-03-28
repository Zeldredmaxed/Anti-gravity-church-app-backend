import React, { useState, useEffect } from 'react';
import './EventsView.css';
import { 
  ChevronDown, 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  Plus, 
  Calendar, 
  IdCard, 
  User, 
  UserPlus, 
  Link as LinkIcon, 
  CheckCircle,
  Circle
} from 'lucide-react';
import { eventsService } from '../api/services/events.service';
import type { EventResponse } from '../api/services/events.service';
import { dashboardService } from '../api/services/dashboard.service';

export const EventsView: React.FC = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [currentDate, setCurrentDate] = useState(new Date());
    const [events, setEvents] = useState<EventResponse[]>([]);
    const [upcomingCount, setUpcomingCount] = useState(0);
    const [totalMembers, setTotalMembers] = useState(203); // Initial fake, updated below
    const [selectedEvent, setSelectedEvent] = useState<EventResponse | null>(null);

    useEffect(() => {
        const fetchEventData = async () => {
            try {
                // Fetch events
                const allEvents = await eventsService.getEvents({ include_past: true });
                setEvents(allEvents);
                
                // Fetch metrics purely for total members
                const metrics = await dashboardService.getMetrics();
                setTotalMembers(metrics.members.total);
                
                // Get upcoming specifically
                const upcoming = await eventsService.getEvents();
                setUpcomingCount(upcoming.length);

            } catch (error) {
                console.error("Error fetching event data", error);
            }
        };
        fetchEventData();
    }, [currentDate]);

    // Calendar logic
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstDayOfMonth = new Date(year, month, 1).getDay();

    const days = [];
    for (let i = 0; i < firstDayOfMonth; i++) {
        days.push(null);
    }
    for (let i = 1; i <= daysInMonth; i++) {
        days.push(i);
    }
    
    const totalCells = Math.ceil(days.length / 7) * 7;
    for (let i = days.length; i < totalCells; i++) {
        days.push(null);
    }

    const prevMonth = () => {
        setCurrentDate(new Date(year, month - 1, 1));
    };

    const nextMonth = () => {
        setCurrentDate(new Date(year, month + 1, 1));
    };

    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

    const getEventsForDay = (day: number) => {
        return events.filter(e => {
            const dateObj = new Date(e.start_datetime);
            return dateObj.getFullYear() === year && dateObj.getMonth() === month && dateObj.getDate() === day;
        });
    };

    const handleEventClick = (e: React.MouseEvent, evt: EventResponse) => {
        e.stopPropagation();
        setSelectedEvent(evt);
        setIsModalOpen(true);
    };

    return (
        <div className="events-dashboard fade-in">
            <div className="sub-header flex-between">
                <div className="title-section">
                    <div className="page-title">
                        <h1>Church Events Calendar</h1>
                    </div>
                    <div className="filters">
                        <div className="filter-btn">
                            Month View <ChevronDown size={14} />
                        </div>
                        <div className="filter-btn">
                            Category <ChevronDown size={14} />
                        </div>
                    </div>
                </div>
                <div className="actions">
                    <div className="search-bar">
                        <Search size={18} color="#888" />
                        <input type="text" placeholder="Search Events" />
                    </div>
                    <button className="btn-add">Add Event</button>
                </div>
            </div>

            <div className="main-content">
                {/* --- Left Sidebar --- */}
                <div className="left-sidebar">
                    <div className="glass-panel stat-card">
                        <div className="stat-grid">
                            <div className="stat-item">
                                <h2>{upcomingCount}</h2>
                                <p>Upcoming<br/>Events</p>
                            </div>
                            <div className="stat-item">
                                <h2>56</h2>
                                <p>Total Volunteers</p>
                            </div>
                        </div>
                        <div className="stat-full">
                            <h2>{totalMembers}</h2>
                            <p>Members</p>
                        </div>
                    </div>

                    <div className="glass-panel donut-card">
                        <h3>Volunteer Coverage</h3>
                        <div className="donut-chart">
                            <div className="donut-inner">75%</div>
                        </div>
                    </div>

                    <div className="glass-panel progress-card">
                        <div className="progress-item">
                            <div className="prog-header"><span>Donation Goal</span><span>90%</span></div>
                            <div className="prog-bar-bg"><div className="prog-bar-fill fill-dark"></div></div>
                        </div>
                        <div className="progress-item">
                            <div className="prog-header"><span>New Guest Follow-up</span><span>15%</span></div>
                            <div className="prog-bar-bg"><div className="prog-bar-fill fill-yellow"></div></div>
                        </div>
                    </div>
                </div>

                {/* --- Center Calendar --- */}
                <div className="glass-panel calendar-container">
                    <div className="cal-header">
                        <button className="cal-nav-btn" onClick={prevMonth}><ChevronLeft size={16} /></button>
                        <h2>{monthNames[month]} {year}</h2>
                        <button className="cal-nav-btn" onClick={nextMonth}><ChevronRight size={16} /></button>
                    </div>

                    <div className="calendar-grid">
                        <div className="cal-day-header">Sun</div>
                        <div className="cal-day-header">Mon</div>
                        <div className="cal-day-header">Tue</div>
                        <div className="cal-day-header">Wed</div>
                        <div className="cal-day-header">Thu</div>
                        <div className="cal-day-header">Fri</div>
                        <div className="cal-day-header">Sat</div>

                        {days.map((day, ix) => {
                            const todayStr = new Date().toDateString();
                            const isToday = day !== null && new Date(year, month, day).toDateString() === todayStr;
                            const dayEvents = day !== null ? getEventsForDay(day) : [];

                            return (
                                <div key={ix} className={`cal-cell ${day === null ? 'bg-lighter' : ''} ${isToday ? 'active-day' : ''}`}>
                                    {day !== null && <span className="date-num">{day}</span>}
                                    {dayEvents.map(evt => (
                                        <div 
                                            key={evt.id} 
                                            className="evt-chip bg-yellow" style={{ cursor: 'pointer' }}
                                            onClick={(e) => handleEventClick(e, evt)}
                                        >
                                            {evt.title}
                                        </div>
                                    ))}
                                    {day !== null && dayEvents.length === 0 && (
                                        <div className="hover-plus"><Plus size={24} /></div>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    {isModalOpen && selectedEvent && (
                        <div className="modal-overlay">
                            <h3>Edit Event: {selectedEvent.title}</h3>
                            
                            <div className="form-group">
                                <label>Event Name</label>
                                <input type="text" className="form-input" defaultValue={selectedEvent.title} />
                            </div>
                            
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Date</label>
                                    <div className="input-with-icon">
                                        <input type="text" className="form-input" defaultValue={new Date(selectedEvent.start_datetime).toDateString()} />
                                        <Calendar size={14} />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label>Time</label>
                                    <div className="input-with-icon">
                                        <input type="text" className="form-input" defaultValue={new Date(selectedEvent.start_datetime).toLocaleTimeString()} />
                                        <ChevronDown size={14} />
                                    </div>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Description</label>
                                <textarea className="form-input" defaultValue={selectedEvent.description || 'No description provided.'}></textarea>
                            </div>

                            <div className="form-group" style={{ marginTop: '10px' }}>
                                <label>RSVP Count: <strong>{selectedEvent.rsvp_count || 0}</strong></label>
                            </div>

                            <div className="modal-actions">
                                <button className="btn-outline">RSVP List</button>
                                <div style={{display: 'flex', gap: '12px', alignItems: 'center'}}>
                                    <button className="btn-save" onClick={() => setIsModalOpen(false)}>Save</button>
                                    <button className="btn-text" onClick={() => setIsModalOpen(false)}>Cancel</button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* --- Right Sidebar --- */}
                <div className="right-sidebar">
                    <div className="glass-panel onboarding-card">
                        <div className="onboarding-header">
                            <h3>Onboarding</h3>
                            <h2>18%</h2>
                        </div>
                        
                        <div className="segmented-bar">
                            <span className="seg-label" style={{ left: '0' }}>30%</span>
                            <span className="seg-label" style={{ left: '50%' }}>25%</span>
                            <span className="seg-label" style={{ left: '85%' }}>0%</span>
                            
                            <div className="seg-part seg-yellow">Task</div>
                            <div className="seg-part seg-dark"></div>
                            <div className="seg-part seg-empty"></div>
                        </div>

                        <div className="task-list">
                            <div className="task-item">
                                <div className="task-icon"><IdCard size={16} /></div>
                                <div className="task-info">
                                    <h4>First Visit</h4>
                                    <p>Sep 13, 08:30</p>
                                </div>
                                <CheckCircle size={16} className="check-icon active" />
                            </div>
                            <div className="task-item">
                                <div className="task-icon"><User size={16} /></div>
                                <div className="task-info">
                                    <h4>Membership Class</h4>
                                    <p>Sep 13, 10:50</p>
                                </div>
                                <Circle size={16} className="check-icon" />
                            </div>
                            <div className="task-item">
                                <div className="task-icon"><UserPlus size={16} /></div>
                                <div className="task-info">
                                    <h4>Volunteer Training</h4>
                                    <p>Sep 13, 14:45</p>
                                </div>
                                <Circle size={16} className="check-icon" />
                            </div>
                            <div className="task-item">
                                <div className="task-icon"><LinkIcon size={16} /></div>
                                <div className="task-info">
                                    <h4>HR Policy Review</h4>
                                    <p>Sep 13, 16:30</p>
                                </div>
                                <Circle size={16} className="check-icon" />
                            </div>
                        </div>
                    </div>

                    <div className="glass-panel bookings-card">
                        <h3>Upcoming Events Quick View</h3>
                        <div className="booking-list">
                            {events.slice(0, 3).map((evt) => (
                                <div className="booking-item" key={evt.id}>
                                    <img src={evt.cover_image_url || "https://images.unsplash.com/photo-1543862809-2c9e0bcebc10?ixlib=rb-4.0.3&auto=format&fit=crop&w=100&q=80"} alt="Event" />
                                    <div className="booking-info">
                                        <h4>{evt.title}</h4>
                                        <p>{new Date(evt.start_datetime).toLocaleDateString()}</p>
                                    </div>
                                    <ChevronRight size={14} className="text-gray" />
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};
