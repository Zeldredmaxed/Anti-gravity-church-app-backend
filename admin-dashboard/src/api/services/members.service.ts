import { apiClient } from '../client';

export interface Member {
  id: number;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  membership_status: string;
  join_date: string | null;
  // Other fields available from backend depending on MemberResponse
}

export interface MemberListResponse {
  items: Member[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export const membersService = {
  async getMembers(params?: {
    search?: string;
    membership_status?: string;
    page?: number;
    per_page?: number;
  }): Promise<MemberListResponse> {
    const response = await apiClient.get<MemberListResponse>('/api/v1/members', {
      params,
    });
    return response.data;
  },

  async getMember(id: number): Promise<Member> {
    const response = await apiClient.get<Member>(`/api/v1/members/${id}`);
    return response.data;
  },
};
