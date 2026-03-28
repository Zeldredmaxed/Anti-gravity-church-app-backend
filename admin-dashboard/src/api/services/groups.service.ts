import { apiClient } from '../client';

export interface GroupResponse {
    id: number;
    name: string;
    description?: string;
    group_type: string;
    leader_id?: number;
    leader_name?: string;
    meeting_day?: string;
    meeting_time?: string;
    meeting_location?: string;
    is_active: boolean;
    max_capacity?: number;
    member_count: number;
    campus?: string;
    created_at: string;
}

export interface GroupMemberResponse {
    id: number;
    member_id: number;
    member_name: string;
    role: string;
    joined_date: string;
}

export interface GroupDetailResponse extends GroupResponse {
    members: GroupMemberResponse[];
}

export interface GroupCreate {
    name: string;
    description?: string;
    group_type: string;
    leader_id?: number;
    meeting_day?: string;
    meeting_time?: string;
    meeting_location?: string;
    is_active?: boolean;
    max_capacity?: number;
    campus?: string;
}

export interface GroupUpdate extends Partial<GroupCreate> {}

export interface GroupMemberAdd {
    member_id: number;
    role: string;
}

export const groupsService = {
    getGroups: async (params?: { group_type?: string; is_active?: boolean }): Promise<GroupResponse[]> => {
        const response = await apiClient.get('/api/v1/groups', { params });
        return response.data;
    },

    getGroup: async (id: number): Promise<GroupDetailResponse> => {
        const response = await apiClient.get(`/api/v1/groups/${id}`);
        return response.data;
    },

    createGroup: async (data: GroupCreate): Promise<GroupResponse> => {
        const response = await apiClient.post('/api/v1/groups', data);
        return response.data;
    },

    updateGroup: async (id: number, data: GroupUpdate): Promise<GroupResponse> => {
        const response = await apiClient.put(`/api/v1/groups/${id}`, data);
        return response.data;
    },

    addMember: async (groupId: number, data: GroupMemberAdd): Promise<{ message: string; membership_id: number }> => {
        const response = await apiClient.post(`/api/v1/groups/${groupId}/members`, data);
        return response.data;
    },

    removeMember: async (groupId: number, memberId: number): Promise<void> => {
        await apiClient.delete(`/api/v1/groups/${groupId}/members/${memberId}`);
    }
};
