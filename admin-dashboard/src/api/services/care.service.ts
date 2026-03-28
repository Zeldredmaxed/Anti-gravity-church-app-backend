import apiClient from '../client';

export interface CareLeader {
  id: string;
  name: string;
  avatar_url: string | null;
}

export interface CareResponse {
  id: string;
  requester_id: string;
  requester_name?: string;
  requester_avatar?: string;
  case_type: string;
  sub_type: string | null;
  status: string;
  priority: string;
  description: string | null;
  assigned_to: string | null;
  assigned_leader?: CareLeader | null;
  created_at: string;
  updated_at: string;
}

export interface CreateCareCaseRequest {
  requester_id: string;
  case_type: string;
  sub_type?: string;
  priority?: string;
  description?: string;
}

export const careService = {
  getAllCareCases: async (skip: number = 0, limit: number = 100): Promise<CareResponse[]> => {
    const { data } = await apiClient.get<CareResponse[]>(`/care/?skip=${skip}&limit=${limit}`);
    return data;
  },

  getCareCase: async (id: string): Promise<CareResponse> => {
    const { data } = await apiClient.get<CareResponse>(`/care/${id}`);
    return data;
  },

  createCareCase: async (caseData: CreateCareCaseRequest): Promise<CareResponse> => {
    const { data } = await apiClient.post<CareResponse>('/care/', caseData);
    return data;
  },

  updateCareCaseStatus: async (id: string, status: string): Promise<CareResponse> => {
    const { data } = await apiClient.put<CareResponse>(`/care/${id}/status`, { status });
    return data;
  },

  assignCareCase: async (id: string, assigned_to: string): Promise<CareResponse> => {
    const { data } = await apiClient.put<CareResponse>(`/care/${id}/assign`, { assigned_to });
    return data;
  },

  deleteCareCase: async (id: string): Promise<void> => {
    await apiClient.delete(`/care/${id}`);
  }
};
