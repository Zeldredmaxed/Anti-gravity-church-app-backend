import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import './Layout.css';

export function Layout() {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <>
      <header className="app-header">
        <div className="logo cursor-pointer" onClick={() => navigate('/')}>
          <i className="fa-solid fa-church"></i> FaithWorks CRM
        </div>
        
        <div className="nav-pills">
          <NavLink to="/" className={({isActive}) => clsx("nav-pill", isActive && "active")}>Dashboard</NavLink>
          <NavLink to="/people" className={({isActive}) => clsx("nav-pill", isActive && "active")}>People</NavLink>
          <NavLink to="/giving" className={({isActive}) => clsx("nav-pill", isActive && "active")}>Giving</NavLink>
          <NavLink to="/attendance" className={({isActive}) => clsx("nav-pill", isActive && "active")}>Attendance</NavLink>
          <NavLink to="/events" className={({isActive}) => clsx("nav-pill", isActive && "active")}>Events</NavLink>
          <NavLink to="/groups" className={({isActive}) => clsx("nav-pill", isActive && "active")}>Groups</NavLink>
          <NavLink to="/care" className={({isActive}) => clsx("nav-pill", isActive && "active")}>Care</NavLink>
          <NavLink to="/volunteers" className={({isActive}) => clsx("nav-pill", isActive && "active")}>Volunteers</NavLink>
          <NavLink to="/settings" className={({isActive}) => clsx("nav-pill", isActive && "active")}>Settings</NavLink>
        </div>

        <div className="header-actions">
          <button className="icon-btn"><i className="fa-regular fa-bell"></i></button>
          <button className="icon-btn" style={{ position: 'relative' }}>
            <i className="fa-regular fa-envelope"></i>
            <div className="notification-dot" style={{ position: 'absolute', top: 10, right: 10, width: 8, height: 8, background: '#dcb34a', borderRadius: '50%' }}></div>
          </button>
          
          <div className="relative">
            <img 
              src="https://i.pravatar.cc/150?img=11" 
              alt="Profile" 
              className="avatar" 
              style={{ width: 40, height: 40, borderRadius: '50%', objectFit: 'cover', cursor: 'pointer' }}
              onClick={() => setDropdownOpen(!dropdownOpen)}
            />
            {dropdownOpen && (
              <div className="dropdown right" style={{ position: 'absolute', right: 0, top: 50, background: 'white', borderRadius: 12, padding: '10px 0', width: 150, zIndex: 10, boxShadow: '0 4px 15px rgba(0,0,0,0.1)' }}>
                <div className="dropdown-item" onClick={() => {navigate('/profile'); setDropdownOpen(false)}} style={{ padding: '8px 15px', fontSize: 13, cursor: 'pointer' }}>View Profile</div>
                <div className="dropdown-item" onClick={() => {navigate('/settings'); setDropdownOpen(false)}} style={{ padding: '8px 15px', fontSize: 13, cursor: 'pointer' }}>Settings</div>
                <div className="dropdown-item" onClick={() => { /* Logout implementation here */ setDropdownOpen(false)}} style={{ padding: '8px 15px', fontSize: 13, cursor: 'pointer' }}>Logout</div>
              </div>
            )}
          </div>
        </div>
      </header>
      
      {/* Route Content Starts Here */}
      <Outlet />
    </>
  );
}
