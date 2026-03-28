import { apiClient } from '../client';

export interface Donation {
  id: number;
  donor_id?: number;
  donor_name?: string;
  fund_id: number;
  fund_name?: string;
  amount: string | number;
  donation_type: string;
  payment_method: string;
  check_number?: string;
  transaction_id?: string;
  date: string;
  is_recurring: boolean;
  recurring_frequency?: string;
  is_anonymous: boolean;
  notes?: string;
  created_at: string;
}

export interface DonationListResponse {
  items: Donation[];
  total: number;
  page: number;
  per_page: number;
  total_amount: number;
}

export const givingService = {
  getDonations: async (params?: { page?: number; per_page?: number; fund_id?: number }): Promise<DonationListResponse> => {
    const response = await apiClient.get<DonationListResponse>('/api/v1/donations', { params });
    return response.data;
  },
};
