import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Squares2X2Icon, 
  UsersIcon, 
  BanknotesIcon,
  CalendarIcon,
  ChatBubbleLeftRightIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'; // Need to install @heroicons/react

export const Sidebar: React.FC = () => {
  const navigation = [
    { name: 'Dashboard', href: '/', icon: Squares2X2Icon },
    { name: 'Members', href: '/members', icon: UsersIcon },
    { name: 'Giving', href: '/giving', icon: BanknotesIcon },
    { name: 'Events', href: '/events', icon: CalendarIcon },
    { name: 'Communications', href: '/communications', icon: ChatBubbleLeftRightIcon },
    { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
  ];

  return (
    <div style={{
      width: 'var(--sidebar-width)',
      height: '100vh',
      position: 'fixed',
      top: 0,
      left: 0,
      background: 'var(--glass-bg)',
      backdropFilter: 'blur(12px)',
      borderRight: '1px solid var(--border-light)',
      padding: '2rem 1rem',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div style={{ marginBottom: '3rem', padding: '0 1rem' }}>
        <h2 style={{ 
          fontSize: '1.5rem', 
          fontWeight: '700',
          background: 'var(--accent-gradient)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '-0.025em'
        }}>
          ChMS Admin
        </h2>
      </div>

      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            style={({ isActive }: { isActive: boolean }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-md)',
              color: isActive ? 'white' : 'var(--text-secondary)',
              background: isActive ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
              fontWeight: isActive ? 600 : 500,
              textDecoration: 'none',
              transition: 'all 0.2s ease',
              border: isActive ? '1px solid rgba(139, 92, 246, 0.3)' : '1px solid transparent',
            })}
          >
            <item.icon style={{ width: '1.5rem', height: '1.5rem' }} />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-light)' }}>
        <div style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '2rem',
            height: '2rem',
            borderRadius: '50%',
            background: 'var(--accent-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '0.875rem'
          }}>
            A
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>Admin User</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Pastor</div>
          </div>
        </div>
      </div>
    </div>
  );
};
