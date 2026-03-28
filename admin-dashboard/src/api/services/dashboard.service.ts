import { apiClient } from '../client';

export interface DashboardMetrics {
  giving: { total: number; trend: number };
  attendance: { total: number; trend: number };
  groups: { total: number; trend: number };
  members: { total: number; trend: number };
}

export interface DashboardEvent {
  id: number;
  title: string;
  date: string | null;
  location: string | null;
}

export interface DashboardActivity {
  id: number;
  action: string;
  target: string;
  time: string;
}

export const dashboardService = {
  async getMetrics(): Promise<DashboardMetrics> {
    const response = await apiClient.get<DashboardMetrics>('/api/v1/dashboard/metrics');
    return response.data;
  },

  async getUpcomingEvents(limit = 5): Promise<DashboardEvent[]> {
    const response = await apiClient.get<DashboardEvent[]>('/api/v1/dashboard/events', {
      params: { limit },
    });
    return response.data;
  },

  async getActivityFeed(limit = 5): Promise<DashboardActivity[]> {
    const response = await apiClient.get<DashboardActivity[]>('/api/v1/dashboard/activity', {
      params: { limit },
    });
    return response.data;
  },
};
