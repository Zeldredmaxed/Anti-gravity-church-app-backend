import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { 
  UsersIcon, 
  CurrencyDollarIcon,
  CheckCircleIcon,
  HeartIcon 
} from '@heroicons/react/24/outline';

interface DashboardMetrics {
  total_active_members: number;
  mtd_giving: number;
  pending_tasks: number;
  pending_prayers: number;
}

export const DashboardHome: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await apiClient.get<DashboardMetrics>('/admin/dashboard/metrics');
        setMetrics(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load dashboard metrics');
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <div style={{
          width: '3rem',
          height: '3rem',
          border: '3px solid rgba(139, 92, 246, 0.2)',
          borderTopColor: 'var(--accent-primary)',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger)' }}>
        <h2>Error Loading Dashboard</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', marginBottom: '0.5rem' }}>Welcome back, Pastor</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Here is what's happening in your church today.</p>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', 
        gap: '1.5rem',
        marginBottom: '3rem'
      }}>
        {/* Members Card */}
        <div className="glass-card delay-100" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ padding: '0.75rem', background: 'rgba(59, 130, 246, 0.1)', borderRadius: 'var(--radius-md)', color: 'var(--info)' }}>
              <UsersIcon style={{ width: '1.5rem', height: '1.5rem' }} />
            </div>
            <span className="badge badge-success">+2.4%</span>
          </div>
          <div>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, lineHeight: 1 }}>
              {metrics?.total_active_members.toLocaleString()}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Active Members
            </div>
          </div>
        </div>

        {/* Giving Card */}
        <div className="glass-card delay-200" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ padding: '0.75rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: 'var(--radius-md)', color: 'var(--success)' }}>
              <CurrencyDollarIcon style={{ width: '1.5rem', height: '1.5rem' }} />
            </div>
            <span className="badge badge-warning">On Track</span>
          </div>
          <div>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, lineHeight: 1 }}>
              ${metrics?.mtd_giving.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
              MTD Giving
            </div>
          </div>
        </div>

        {/* Action Items Card */}
        <div className="glass-card delay-300" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ padding: '0.75rem', background: 'rgba(245, 158, 11, 0.1)', borderRadius: 'var(--radius-md)', color: 'var(--warning)' }}>
              <CheckCircleIcon style={{ width: '1.5rem', height: '1.5rem' }} />
            </div>
            {metrics?.pending_tasks && metrics.pending_tasks > 5 ? (
              <span className="badge badge-warning">Action Needed</span>
            ) : null}
          </div>
          <div>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, lineHeight: 1 }}>
              {metrics?.pending_tasks}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Pending Tasks
            </div>
          </div>
        </div>

        {/* Prayers Card */}
        <div className="glass-card delay-300" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
             <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ padding: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: 'var(--radius-md)', color: 'var(--danger)' }}>
              <HeartIcon style={{ width: '1.5rem', height: '1.5rem' }} />
            </div>
          </div>
          <div>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, lineHeight: 1 }}>
              {metrics?.pending_prayers}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Pending Prayer Requests
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
