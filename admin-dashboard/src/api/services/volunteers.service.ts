import apiClient from '../client';

export interface Volunteer {
  id: string;
  name: string;
  avatar: string;
  role: string;
  available: boolean;
  team: string;
  contact: string;
}

export const volunteersService = {
  getVolunteerList: async (): Promise<Volunteer[]> => {
    const { data } = await apiClient.get<Volunteer[]>('/volunteers/list');
    return data;
  }
};
