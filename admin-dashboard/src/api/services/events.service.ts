import { apiClient } from '../client';

export interface EventResponse {
    id: number;
    church_id: number;
    title: string;
    description: string | null;
    event_type: string;
    location: string | null;
    start_datetime: string;
    end_datetime: string | null;
    is_recurring: boolean;
    recurrence_rule: string | null;
    max_capacity: number | null;
    rsvp_count: number;
    registration_required: boolean;
    cover_image_url: string | null;
    is_published: boolean;
    is_cancelled: boolean;
    created_by: number | null;
    created_at: string;
    my_rsvp?: string | null;
}

export const eventsService = {
    getEvents: async (params?: { include_past?: boolean; event_type?: string; limit?: number; offset?: number }): Promise<EventResponse[]> => {
        const response = await apiClient.get<EventResponse[]>('/api/v1/events', { params });
        return response.data;
    },
    
    getEvent: async (id: number): Promise<EventResponse> => {
        const response = await apiClient.get<EventResponse>(`/api/v1/events/${id}`);
        return response.data;
    }
};
