import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { useAuth } from '../contexts/AuthContext';

export const Layout: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <header style={{ 
          height: 'var(--header-height)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'flex-end',
          paddingBottom: '2rem'
        }}>
          {/* Topbar for future global search, notifications, user profile */}
        </header>
        <Outlet />
      </main>
    </div>
  );
};
