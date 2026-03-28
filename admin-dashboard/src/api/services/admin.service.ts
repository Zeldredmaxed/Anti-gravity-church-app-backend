import { apiClient } from '../client';

export interface ChurchSettings {
  church_name: string;
  church_address: string;
  church_phone: string;
  church_email: string;
  church_website: string;
}

export const adminService = {
  getSettings: async (): Promise<ChurchSettings> => {
    const { data } = await apiClient.get<ChurchSettings>('/admin/settings');
    return data;
  },

  getCurrentUser: async (): Promise<any> => {
    const { data } = await apiClient.get('/auth/me');
    return data;
  }
};
